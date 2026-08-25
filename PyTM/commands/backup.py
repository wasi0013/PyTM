import os

import click

from PyTM import settings
from PyTM.console import console
from PyTM.core import backup_handler, data_handler


def _repo_root():
    return os.path.abspath(settings.data_folder)


def _backup_config(state):
    return state.setdefault("config", {}).setdefault("backup", {})


@click.group(invoke_without_command=True)
@click.pass_context
def backup(ctx):
    """
    - pytm sub-commands for git-based local backup of your data.
    """
    # Explicit no-args-is-help handling: see `config`/`invoice`/`hook`
    # groups for why this isn't left to Click's own default.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@backup.command()
def enable():
    """
    - turns on git auto-backup: ~/.pytm becomes its own git repo and
      every write is committed automatically. Commit-only by default —
      no remote is configured; add one with `pytm backup remote set`.
    """
    if not backup_handler.is_git_available():
        raise click.ClickException(
            "git isn't installed or isn't on PATH. Install git and try again."
        )
    repo_root = _repo_root()
    if not backup_handler.init_repo(repo_root):
        raise click.ClickException(f"Failed to initialize a git repo at {repo_root}.")
    state = data_handler.load_data(settings.state_filepath)
    _backup_config(state)["enabled"] = True
    data_handler.save_data(state, settings.state_filepath)
    console.print(
        f"[green]Backup enabled.[/green] {repo_root} is now a git repo; "
        "every write is committed automatically."
    )
    console.print(
        "[i]No remote configured — this stays local-only until you run "
        "`pytm backup remote set URL`.[/i]"
    )


@backup.command()
def disable():
    """
    - turns off auto-commit. Existing history and any configured remote
      are left untouched.
    """
    repo_root = _repo_root()
    # Flush anything pending while backup is still enabled, so turning it
    # off doesn't leave the most recent write uncommitted.
    backup_handler.commit_all(repo_root, "PyTM backup: flush before disabling")
    state = data_handler.load_data(settings.state_filepath)
    _backup_config(state)["enabled"] = False
    data_handler.save_data(state, settings.state_filepath)
    # The save above triggers no auto-commit (enabled is now False), so
    # the disable itself is recorded explicitly here instead.
    backup_handler.commit_all(repo_root, "PyTM backup: disabled")
    console.print("[yellow]Backup disabled.[/yellow] Existing history is untouched.")


@backup.command()
def commit():
    """
    - manually flushes any uncommitted changes to the backup repo. Works
      whether or not auto-backup is currently enabled.
    """
    repo_root = _repo_root()
    if not backup_handler.is_repo(repo_root):
        raise click.ClickException(
            "No backup repo yet. Run `pytm backup enable` first."
        )
    if not backup_handler.commit_all(repo_root, "PyTM backup: manual commit"):
        raise click.ClickException("Commit failed, or timed out waiting on a lock.")
    console.print("[green]Backup repo is up to date.[/green]")


@backup.command()
def status():
    """
    - shows backup status: enabled/disabled, repo state, remote, last
      commit.
    """
    repo_root = _repo_root()
    state = data_handler.load_data(settings.state_filepath)
    cfg = state.get("config", {}).get("backup", {})
    enabled = bool(cfg.get("enabled"))
    console.print(
        "Auto-backup: "
        + ("[green]enabled[/green]" if enabled else "[yellow]disabled[/yellow]")
    )
    if not backup_handler.is_repo(repo_root):
        console.print("[i]No git repo yet. Run `pytm backup enable`.[/i]")
        return
    console.print(f"Repo: [blue]{repo_root}[/blue]")
    dirty = backup_handler.has_uncommitted_changes(repo_root)
    if dirty is None:
        console.print("[red]Could not read git status.[/red]")
    else:
        console.print(
            "Working tree: "
            + (
                "[yellow]uncommitted changes[/yellow]"
                if dirty
                else "[green]clean[/green]"
            )
        )
    commit_info = backup_handler.last_commit_info(repo_root)
    if commit_info:
        console.print(
            f"Last commit: [bold]{commit_info['hash'][:8]}[/bold] "
            f"{commit_info['date']} — {commit_info['message']}"
        )
    else:
        console.print("[i]No commits yet.[/i]")
    remote_name = cfg.get("remote_name")
    if remote_name:
        url = backup_handler.get_remote_url(repo_root, remote_name)
        console.print(
            f"Remote: [blue]{remote_name}[/blue] -> {url or '[red]missing[/red]'}"
        )
    else:
        console.print(
            "[i]No remote configured. `pytm backup remote set URL` to add one.[/i]"
        )


@backup.group(name="remote", invoke_without_command=True)
@click.pass_context
def remote(ctx):
    """
    - pytm sub-commands for configuring a backup remote.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@remote.command("set")
@click.argument("url")
@click.option("--name", default=None, help="Remote name (default: origin).")
def remote_set(url, name):
    """
    - adds (or updates) the git remote backup pushes to. Does not push;
      run `pytm backup push` explicitly.
    """
    name = name or settings.DEFAULT_BACKUP_REMOTE
    repo_root = _repo_root()
    if not backup_handler.is_repo(repo_root):
        raise click.ClickException(
            "No backup repo yet. Run `pytm backup enable` first."
        )
    if not backup_handler.set_remote(repo_root, url, name):
        raise click.ClickException("Failed to configure remote.")
    state = data_handler.load_data(settings.state_filepath)
    _backup_config(state)["remote_name"] = name
    data_handler.save_data(state, settings.state_filepath)
    console.print(
        f"[green]Remote '{name}' set to {url}.[/green] "
        "Run `pytm backup push` to push."
    )


@remote.command("remove")
@click.option("--name", default=None, help="Remote name (default: origin).")
def remote_remove(name):
    """
    - removes a configured git remote.
    """
    name = name or settings.DEFAULT_BACKUP_REMOTE
    repo_root = _repo_root()
    backup_handler.remove_remote(repo_root, name)
    state = data_handler.load_data(settings.state_filepath)
    cfg = _backup_config(state)
    if cfg.get("remote_name") == name:
        cfg["remote_name"] = None
    data_handler.save_data(state, settings.state_filepath)
    console.print(f"[yellow]Remote '{name}' removed.[/yellow]")


@backup.command()
@click.option(
    "--name",
    "remote_name",
    default=None,
    help="Remote name (defaults to the configured one, or 'origin').",
)
@click.option(
    "--branch", default=None, help="Branch to push (defaults to the current branch)."
)
def push(remote_name, branch):
    """
    - pushes the backup repo to its configured remote. Manual only:
      auto-backup commits locally but never pushes on its own.
    """
    repo_root = _repo_root()
    if not backup_handler.is_repo(repo_root):
        raise click.ClickException(
            "No backup repo yet. Run `pytm backup enable` first."
        )
    state = data_handler.load_data(settings.state_filepath)
    cfg = state.get("config", {}).get("backup", {})
    name = remote_name or cfg.get("remote_name") or settings.DEFAULT_BACKUP_REMOTE
    ok, message = backup_handler.push(repo_root, name=name, branch=branch)
    if not ok:
        raise click.ClickException(message)
    console.print(f"[green]{message}[/green]")
