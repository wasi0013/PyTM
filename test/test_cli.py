"""
Tests for `PyTM` module.
"""
from PyTM import __version__
from PyTM.cli import cli
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
