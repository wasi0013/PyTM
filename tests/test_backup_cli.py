import subprocess

from click.testing import CliRunner

from PyTM import settings
from PyTM.cli import cli
from PyTM.core import backup_handler, data_handler


def make_bare_remote(tmp_path, name="remote.git"):
    remote = tmp_path / name
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    return str(remote)


def test_backup_group_no_args_shows_help(pytm_home):
    result = CliRunner().invoke(cli, ["backup"])
    assert result.exit_code == 0
    assert "backup" in result.output.lower()


def test_backup_enable_initializes_repo_and_flag(pytm_home):
    result = CliRunner().invoke(cli, ["backup", "enable"])
    assert result.exit_code == 0, result.output
    assert "Backup enabled" in result.output
    assert backup_handler.is_repo(str(pytm_home)) is True
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["backup"]["enabled"] is True


def test_backup_enable_without_git_errors_cleanly(pytm_home, monkeypatch):
    monkeypatch.setattr(backup_handler, "is_git_available", lambda: False)
    result = CliRunner().invoke(cli, ["backup", "enable"])
    assert result.exit_code != 0
    assert "git" in result.output.lower()
    state = data_handler.load_data(settings.state_filepath)
    assert state.get("config", {}).get("backup", {}).get("enabled") is not True


def test_writes_after_enable_are_auto_committed(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    result = runner.invoke(cli, ["project", "start", "proj-a"])
    assert result.exit_code == 0, result.output
    assert backup_handler.has_uncommitted_changes(str(pytm_home)) is False
    info = backup_handler.last_commit_info(str(pytm_home))
    assert info is not None
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=str(pytm_home), capture_output=True, text=True
    ).stdout.split()
    assert "data.json" in tracked


def test_backup_status_reports_disabled_before_enable(pytm_home):
    result = CliRunner().invoke(cli, ["backup", "status"])
    assert result.exit_code == 0, result.output
    assert "disabled" in result.output.lower()
    assert "No git repo yet" in result.output


def test_backup_status_reports_enabled_and_clean(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    result = runner.invoke(cli, ["backup", "status"])
    assert result.exit_code == 0, result.output
    assert "enabled" in result.output.lower()
    assert "clean" in result.output.lower()


def test_backup_disable_leaves_a_clean_repo_and_stops_auto_commit(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    result = runner.invoke(cli, ["backup", "disable"])
    assert result.exit_code == 0, result.output
    assert backup_handler.has_uncommitted_changes(str(pytm_home)) is False
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["backup"]["enabled"] is False

    # subsequent writes are no longer auto-committed
    before = backup_handler.last_commit_info(str(pytm_home))
    runner.invoke(cli, ["project", "start", "proj-a"])
    after = backup_handler.last_commit_info(str(pytm_home))
    assert before == after
    assert backup_handler.has_uncommitted_changes(str(pytm_home)) is True


def test_backup_commit_flushes_pending_changes_when_disabled(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    runner.invoke(cli, ["backup", "disable"])
    runner.invoke(cli, ["project", "start", "proj-a"])
    assert backup_handler.has_uncommitted_changes(str(pytm_home)) is True

    result = runner.invoke(cli, ["backup", "commit"])
    assert result.exit_code == 0, result.output
    assert backup_handler.has_uncommitted_changes(str(pytm_home)) is False


def test_backup_commit_without_repo_errors_cleanly(pytm_home):
    result = CliRunner().invoke(cli, ["backup", "commit"])
    assert result.exit_code != 0
    assert "backup enable" in result.output


def test_backup_remote_set_and_status(pytm_home, tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    remote_url = make_bare_remote(tmp_path)
    result = runner.invoke(cli, ["backup", "remote", "set", remote_url])
    assert result.exit_code == 0, result.output
    assert backup_handler.get_remote_url(str(pytm_home)) == remote_url
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["backup"]["remote_name"] == "origin"

    result = runner.invoke(cli, ["backup", "status"])
    assert remote_url in result.output.replace("\n", "")


def test_backup_remote_set_without_repo_errors_cleanly(pytm_home, tmp_path):
    remote_url = make_bare_remote(tmp_path)
    result = CliRunner().invoke(cli, ["backup", "remote", "set", remote_url])
    assert result.exit_code != 0
    assert "backup enable" in result.output


def test_backup_remote_remove(pytm_home, tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    remote_url = make_bare_remote(tmp_path)
    runner.invoke(cli, ["backup", "remote", "set", remote_url])

    result = runner.invoke(cli, ["backup", "remote", "remove"])
    assert result.exit_code == 0, result.output
    assert backup_handler.get_remote_url(str(pytm_home)) is None
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["backup"]["remote_name"] is None


def test_backup_push_round_trips_to_remote(pytm_home, tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    remote_url = make_bare_remote(tmp_path)
    runner.invoke(cli, ["backup", "remote", "set", remote_url])
    runner.invoke(cli, ["project", "start", "proj-a"])

    result = runner.invoke(cli, ["backup", "push"])
    assert result.exit_code == 0, result.output
    assert "Pushed" in result.output

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", remote_url, str(clone)], check=True)
    assert (clone / "data.json").exists()


def test_backup_push_without_remote_errors_cleanly(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    result = runner.invoke(cli, ["backup", "push"])
    assert result.exit_code != 0
    assert "remote" in result.output.lower()


def test_backup_push_without_repo_errors_cleanly(pytm_home):
    result = CliRunner().invoke(cli, ["backup", "push"])
    assert result.exit_code != 0
    assert "backup enable" in result.output


def test_backup_remote_group_no_args_shows_help(pytm_home):
    result = CliRunner().invoke(cli, ["backup", "remote"])
    assert result.exit_code == 0
    assert "remote" in result.output.lower()


def test_backup_enable_reports_init_repo_failure(pytm_home, monkeypatch):
    monkeypatch.setattr(backup_handler, "init_repo", lambda repo_root: False)
    result = CliRunner().invoke(cli, ["backup", "enable"])
    assert result.exit_code != 0
    assert "Failed to initialize" in result.output


def test_backup_enable_reports_initial_commit_failure(pytm_home, monkeypatch):
    monkeypatch.setattr(backup_handler, "commit_all", lambda *a, **k: False)
    result = CliRunner().invoke(cli, ["backup", "enable"])
    assert result.exit_code != 0
    assert "Failed to initialize" in result.output
    state = data_handler.load_data(settings.state_filepath)
    assert state.get("config", {}).get("backup", {}).get("enabled") is not True


def test_backup_commit_reports_commit_all_failure(pytm_home, monkeypatch):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    monkeypatch.setattr(backup_handler, "commit_all", lambda *a, **k: False)
    result = runner.invoke(cli, ["backup", "commit"])
    assert result.exit_code != 0
    assert "Commit failed" in result.output


def test_backup_status_reports_unreadable_git_status(pytm_home, monkeypatch):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    monkeypatch.setattr(
        backup_handler, "has_uncommitted_changes", lambda repo_root: None
    )
    result = runner.invoke(cli, ["backup", "status"])
    assert result.exit_code == 0, result.output
    assert "Could not read git status" in result.output


def test_backup_status_reports_no_commits_yet(pytm_home, monkeypatch):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    monkeypatch.setattr(backup_handler, "last_commit_info", lambda repo_root: None)
    result = runner.invoke(cli, ["backup", "status"])
    assert result.exit_code == 0, result.output
    assert "No commits yet" in result.output


def test_backup_remote_set_reports_set_remote_failure(pytm_home, monkeypatch, tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])
    monkeypatch.setattr(backup_handler, "set_remote", lambda *a, **k: False)
    result = runner.invoke(cli, ["backup", "remote", "set", make_bare_remote(tmp_path)])
    assert result.exit_code != 0
    assert "Failed to configure remote" in result.output


def test_backup_never_touches_unrelated_directories(pytm_home, tmp_path, monkeypatch):
    """
    End-to-end version of the `auto_commit` safety gate: a command that
    writes to a path outside `settings.data_folder` (none of the built-in
    commands do today, but this guards the invariant directly) must never
    invoke git.
    """
    runner = CliRunner()
    runner.invoke(cli, ["backup", "enable"])

    calls = []
    monkeypatch.setattr(
        backup_handler, "_run_git", lambda *a, **k: calls.append(a) or None
    )
    outside = tmp_path / "outside.json"
    data_handler.save_data({"a": 1}, str(outside))
    assert calls == []
