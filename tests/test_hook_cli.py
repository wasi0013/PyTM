import subprocess

from click.testing import CliRunner

from PyTM import settings
from PyTM.cli import cli
from PyTM.core import data_handler


def make_git_repo(path, branch="main"):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=path, check=True)
    return str(path)


def test_hook_link_and_list(pytm_home, tmp_path):
    runner = CliRunner()
    repo = tmp_path / "repo-a"
    repo.mkdir()
    result = runner.invoke(cli, ["hook", "link", "proj-a", "--path", str(repo)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(cli, ["hook", "list"])
    assert result.exit_code == 0, result.output
    assert "proj-a" in result.output

    data = data_handler.load_data()
    assert "proj-a" in data  # link creates the project
    state = data_handler.load_data(settings.state_filepath)
    assert state["hooks"]["links"][str(repo.resolve())] == "proj-a"


def test_hook_unlink(pytm_home, tmp_path):
    runner = CliRunner()
    repo = tmp_path / "repo-a"
    repo.mkdir()
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", str(repo)])
    result = runner.invoke(cli, ["hook", "unlink", "--path", str(repo)])
    assert result.exit_code == 0, result.output
    assert "Unlinked" in result.output

    result = runner.invoke(cli, ["hook", "list"])
    assert "proj-a" not in result.output


def test_hook_unlink_unknown_path_errors_cleanly(pytm_home, tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["hook", "unlink", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "isn't linked" in result.output


def test_hook_resolve_apply_starts_project_and_branch_task(pytm_home, tmp_path):
    runner = CliRunner()
    repo = make_git_repo(tmp_path / "repo-a", branch="feature-x")
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo])

    result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo])
    assert result.exit_code == 0, result.output
    assert result.output == ""  # silent on the happy path

    state = data_handler.load_data(settings.state_filepath)
    assert state[settings.CURRENT_PROJECT] == "proj-a"
    assert state[settings.CURRENT_TASK] == "feature-x"
    data = data_handler.load_data()
    assert data["proj-a"]["tasks"]["feature-x"]["status"] == "running"


def test_hook_resolve_apply_is_idempotent(pytm_home, tmp_path):
    runner = CliRunner()
    repo = make_git_repo(tmp_path / "repo-a", branch="main")
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo])

    for _ in range(3):
        result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo])
        assert result.exit_code == 0, result.output
        assert result.exception is None

    state = data_handler.load_data(settings.state_filepath)
    assert state[settings.CURRENT_TASK] == "main"


def test_hook_resolve_apply_on_unlinked_directory_is_a_noop(pytm_home, tmp_path):
    runner = CliRunner()
    unlinked = tmp_path / "unlinked"
    unlinked.mkdir()
    result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", str(unlinked)])
    assert result.exit_code == 0, result.output
    state = data_handler.load_data(settings.state_filepath)
    assert state.get(settings.CURRENT_PROJECT, "") == ""


def test_hook_resolve_apply_pauses_every_running_task_not_just_current(
    pytm_home, tmp_path
):
    """
    Regression: `resolve --apply` used to pause only `state[CURRENT_TASK]`
    when switching projects. A task left running in project A from an
    earlier visit (not the one `state` points at) kept accruing wall-clock
    time in the background while the hook was tracking project B, and
    that stale time got folded into `duration` the next time it was
    touched — silent, inflated billing.
    """
    runner = CliRunner()
    repo_a = make_git_repo(tmp_path / "repo-a", branch="main")
    repo_b = make_git_repo(tmp_path / "repo-b", branch="main")
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo_a])
    runner.invoke(cli, ["hook", "link", "proj-b", "--path", repo_b])

    runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo_a])
    # A second task is started in A manually — it's running, but it's not
    # the one `state[CURRENT_TASK]` (still "main") points at once we leave.
    runner.invoke(cli, ["task", "start", "other-task"])

    runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo_b])

    data = data_handler.load_data()
    assert data["proj-a"]["tasks"]["main"]["status"] == "paused"
    assert data["proj-a"]["tasks"]["other-task"]["status"] == "paused"


def test_hook_resolve_apply_pauses_stale_running_task_in_incoming_project(
    pytm_home, tmp_path
):
    """
    Regression: `resolve --apply` used to pause running tasks in the
    OUTGOING project only, never checking the INCOMING project for a
    task already left running there (started manually, or by an earlier
    hook resolve that never got to update state before the directory
    changed again). Ordinary usage reproduces it with no crash needed:
    two `task start` calls in a row leave two tasks simultaneously
    running (`task start` never pauses siblings), then `project pause`
    only clears the recorded current task. Resolving into that project
    later must not let the new branch task start running alongside the
    stale one.
    """
    runner = CliRunner()
    repo = make_git_repo(tmp_path / "repo-a", branch="feature-y")

    runner.invoke(cli, ["project", "start", "proj-a"])
    runner.invoke(cli, ["task", "start", "stale-task"])  # left running, untracked
    runner.invoke(cli, ["project", "start", "other-project"])  # state moves on

    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo])
    result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo])
    assert result.exit_code == 0, result.output

    data = data_handler.load_data()
    assert data["proj-a"]["tasks"]["stale-task"]["status"] == "paused"
    assert data["proj-a"]["tasks"]["feature-y"]["status"] == "running"


def test_hook_resolve_apply_pauses_old_projects_task_on_switch(pytm_home, tmp_path):
    runner = CliRunner()
    repo_a = make_git_repo(tmp_path / "repo-a", branch="main")
    repo_b = make_git_repo(tmp_path / "repo-b", branch="main")
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo_a])
    runner.invoke(cli, ["hook", "link", "proj-b", "--path", repo_b])

    runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo_a])
    result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", repo_b])
    assert result.exit_code == 0, result.output

    data = data_handler.load_data()
    assert data["proj-a"]["tasks"]["main"]["status"] == "paused"
    assert data["proj-b"]["tasks"]["main"]["status"] == "running"
    state = data_handler.load_data(settings.state_filepath)
    assert state[settings.CURRENT_PROJECT] == "proj-b"


def test_hook_resolve_dry_run_does_not_mutate_state(pytm_home, tmp_path):
    runner = CliRunner()
    repo = make_git_repo(tmp_path / "repo-a", branch="main")
    runner.invoke(cli, ["hook", "link", "proj-a", "--path", repo])

    result = runner.invoke(cli, ["hook", "resolve", "--path", repo])
    assert result.exit_code == 0, result.output
    assert "proj-a" in result.output

    state = data_handler.load_data(settings.state_filepath)
    assert state.get(settings.CURRENT_PROJECT, "") == ""


def test_hook_group_no_args_shows_help(pytm_home):
    runner = CliRunner()
    result = runner.invoke(cli, ["hook"])
    assert result.exit_code == 0, result.output
    assert "Options" in result.output


def test_hook_resolve_dry_run_reports_no_link(pytm_home, tmp_path):
    runner = CliRunner()
    unlinked = tmp_path / "unlinked"
    unlinked.mkdir()
    result = runner.invoke(cli, ["hook", "resolve", "--path", str(unlinked)])
    assert result.exit_code == 0, result.output
    assert "No link for this directory" in result.output


def test_hook_resolve_apply_swallows_unexpected_errors(
    pytm_home, tmp_path, monkeypatch
):
    """
    `resolve --apply` is invoked from every shell prompt/cd. Whatever goes
    wrong internally, it must exit 0 rather than surface a traceback that
    would show up in the user's interactive shell.
    """
    from PyTM.core import data_handler

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(data_handler, "load_data", boom)
    runner = CliRunner()
    result = runner.invoke(cli, ["hook", "resolve", "--apply", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert result.exception is None
    assert result.output == ""


def test_hook_init_prints_snippet_calling_resolve(pytm_home):
    runner = CliRunner()
    for shell in ("bash", "zsh"):
        result = runner.invoke(cli, ["hook", "init", shell])
        assert result.exit_code == 0, result.output
        assert "pytm hook resolve --apply" in result.output
