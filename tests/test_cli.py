"""
Tests for `PyTM` module.
"""

from PyTM import __version__, settings
from PyTM.cli import cli
from PyTM.core import data_handler
from click.testing import CliRunner


def test_help_exit_successfully():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--help"])
    assert result.exit_code == 0


def test_help_output():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--help"])
    assert "Options" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert __version__ in result.output
    assert result.exit_code == 0
    result = runner.invoke(cli, ["--v"])
    assert __version__ in result.output
    assert result.exit_code == 0
    result = runner.invoke(cli, ["-v"])
    assert __version__ in result.output
    assert result.exit_code == 0


def test_command_project():
    runner = CliRunner()
    result = runner.invoke(cli, ["project"])
    assert result.exit_code == 0


def test_command_task():
    runner = CliRunner()
    result = runner.invoke(cli, ["task"])
    assert result.exit_code == 0


def test_project_summary_does_not_crash(pytm_home):
    """
    Regression test: `pytm project summary NAME` used to crash with
    `TypeError: 'Group' object is not subscriptable` because it referenced
    the bare name `project` (the Click group) instead of the loaded
    project data.
    """
    runner = CliRunner()
    runner.invoke(cli, ["project", "start", "demo"])
    runner.invoke(cli, ["task", "start", "task-a"])
    result = runner.invoke(cli, ["project", "summary", "demo"])
    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert "running" in result.output
    assert "task-a" in result.output


def test_task_rename_does_not_hijack_unrelated_current_task(pytm_home):
    """
    Regression test: renaming a task that isn't the active one used to
    unconditionally overwrite `CURRENT_TASK`, silently switching the
    "active" task to one that was never started.
    """
    runner = CliRunner()
    runner.invoke(cli, ["project", "start", "demo"])
    runner.invoke(cli, ["task", "start", "task-a"])
    runner.invoke(cli, ["task", "pause"])  # clears CURRENT_TASK
    runner.invoke(cli, ["task", "start", "task-b"])  # task-b is now active

    result = runner.invoke(cli, ["task", "rename", "task-a", "task-a-renamed"])
    assert result.exit_code == 0, result.output

    state = data_handler.load_data(settings.state_filepath)
    assert state[settings.CURRENT_TASK] == "task-b"


def test_task_rename_updates_current_task_when_it_is_the_active_task(pytm_home):
    """
    The guard must still update CURRENT_TASK when the renamed task really
    is the active one.
    """
    runner = CliRunner()
    runner.invoke(cli, ["project", "start", "demo"])
    runner.invoke(cli, ["task", "start", "task-a"])

    result = runner.invoke(cli, ["task", "rename", "task-a", "task-a-renamed"])
    assert result.exit_code == 0, result.output

    state = data_handler.load_data(settings.state_filepath)
    assert state[settings.CURRENT_TASK] == "task-a-renamed"


def test_config_user_non_interactive_never_prompts(pytm_home):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "user",
            "--non-interactive",
            "--name",
            "Jane Dev",
            "--hourly-rate",
            "85",
        ],
        input="",  # would hang on a real prompt; proves none were made
    )
    assert result.exit_code == 0, result.output
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["user"]["name"] == "Jane Dev"
    assert state["config"]["user"]["hourly_rate"] == "85"
    assert state["config"]["user"]["email"] == ""  # not passed -> blank default


def test_config_invoice_non_interactive_never_prompts(pytm_home):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["config", "invoice", "--non-interactive", "--title", "Custom Invoice"],
        input="",
    )
    assert result.exit_code == 0, result.output
    state = data_handler.load_data(settings.state_filepath)
    assert state["config"]["invoice"]["title"] == "Custom Invoice"
    assert state["config"]["invoice"]["invoice_number"] == "13"


def test_config_project_non_interactive_never_prompts(pytm_home):
    runner = CliRunner()
    runner.invoke(cli, ["project", "start", "demo"])
    result = runner.invoke(
        cli,
        [
            "config",
            "project",
            "demo",
            "--non-interactive",
            "--title",
            "Demo Project",
            "--not-billable",
            "--client-name",
            "Acme",
        ],
        input="",
    )
    assert result.exit_code == 0, result.output
    data = data_handler.load_data()
    meta = data["demo"]["meta"]
    assert meta["title"] == "Demo Project"
    assert meta["billable"] is False
    assert meta["client_name"] == "Acme"


def test_invoice_auto_non_interactive_on_unconfigured_project(pytm_home):
    """
    Regression test: `invoice auto` used to crash with `KeyError: 'meta'`
    on any project that was never `config project`-ed, since
    `project_handler.create` never sets a `meta` key at all.
    """
    runner = CliRunner()
    runner.invoke(cli, ["project", "start", "demo"])
    runner.invoke(cli, ["task", "start", "billable-work"])
    runner.invoke(cli, ["task", "finish"])

    result = runner.invoke(
        cli,
        [
            "invoice",
            "auto",
            "demo",
            "--non-interactive",
            "--hourly-rate",
            "100",
            "--title",
            "Auto Invoice",
        ],
        input="",
    )
    assert result.exit_code == 0, result.output
    assert result.exception is None
    html_file = pytm_home / "invoices" / "Auto Invoice.html"
    assert html_file.exists()


def test_invoice_manual_non_interactive_with_task_flags(pytm_home):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "invoice",
            "manual",
            "--non-interactive",
            "--title",
            "Manual Invoice",
            "--hourly-rate",
            "100",
            "--task",
            "Design:2:Homepage design",
            "--task",
            "Development:3",
        ],
        input="",
    )
    assert result.exit_code == 0, result.output
    html_file = pytm_home / "invoices" / "Manual Invoice.html"
    assert html_file.exists()
    html = html_file.read_text()
    assert "Design" in html
    assert "Development" in html
    assert "500.00" in html  # (2 + 3) hours * $100/hr subtotal
