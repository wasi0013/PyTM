import os
from functools import partial

import click
from rich.table import Table

from PyTM import settings
from PyTM.console import console
from PyTM.core import data_handler, hook_handler, project_handler, task_handler

BASH_SNIPPET = """\
# pytm ambient tracking hook (bash)
_pytm_hook_check() {
  local _pytm_exit=$?
  local branch=""
  if git rev-parse --git-dir >/dev/null 2>&1; then
    branch="$(git symbolic-ref --short HEAD 2>/dev/null)"
  fi
  if [ "$PWD" != "$_PYTM_LAST_PWD" ] || [ "$branch" != "$_PYTM_LAST_BRANCH" ]; then
    _PYTM_LAST_PWD="$PWD"
    _PYTM_LAST_BRANCH="$branch"
    pytm hook resolve --apply >/dev/null 2>&1
  fi
  return $_pytm_exit
}
case ";$PROMPT_COMMAND;" in
  *";_pytm_hook_check;"*) ;;
  *) PROMPT_COMMAND="_pytm_hook_check;${PROMPT_COMMAND}" ;;
esac
"""

ZSH_SNIPPET = """\
# pytm ambient tracking hook (zsh)
_pytm_hook_check() {
  local branch=""
  if git rev-parse --git-dir >/dev/null 2>&1; then
    branch="$(git symbolic-ref --short HEAD 2>/dev/null)"
  fi
  if [ "$PWD" != "$_PYTM_LAST_PWD" ] || [ "$branch" != "$_PYTM_LAST_BRANCH" ]; then
    _PYTM_LAST_PWD="$PWD"
    _PYTM_LAST_BRANCH="$branch"
    pytm hook resolve --apply >/dev/null 2>&1
  fi
  return 0
}
autoload -Uz add-zsh-hook 2>/dev/null
if typeset -f add-zsh-hook >/dev/null 2>&1; then
  add-zsh-hook precmd _pytm_hook_check
else
  precmd_functions+=(_pytm_hook_check)
fi
"""


@click.group(invoke_without_command=True)
@click.pass_context
def hook(ctx):
    """
    pytm sub-command for ambient tracking (cd / git-branch hooks).
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@hook.command()
@click.argument("project_name")
@click.option(
    "--path",
    default=None,
    help="Directory to link. Defaults to the current directory.",
)
def link(project_name, path):
    """
    - links a directory (and its subdirectories) to a project, so the
      hooks track it automatically. Creates the project if it doesn't
      exist yet.
    """
    target = hook_handler.normalize(path or os.getcwd())
    data_handler.update(partial(project_handler.create, project_name=project_name))
    state = data_handler.load_data(settings.state_filepath)
    links = state.setdefault("hooks", {}).setdefault("links", {})
    links[target] = project_name
    data_handler.save_data(state, settings.state_filepath)
    console.print(
        f"Linked [blue]{target}[/blue] to [bold blue]{project_name}[/bold blue]."
    )


@hook.command()
@click.option(
    "--path",
    default=None,
    help="Directory to unlink. Defaults to the current directory.",
)
def unlink(path):
    """
    - removes a directory's link.
    """
    target = hook_handler.normalize(path or os.getcwd())
    state = data_handler.load_data(settings.state_filepath)
    links = state.get("hooks", {}).get("links", {})
    if target in links:
        del links[target]
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"Unlinked [blue]{target}[/blue].")
    else:
        console.print(f"[red bold]{target} isn't linked.")


@hook.command(name="list")
def list_links():
    """
    - lists all linked directories.
    """
    state = data_handler.load_data(settings.state_filepath)
    links = state.get("hooks", {}).get("links", {})
    if not links:
        console.print(
            "[i]No directories linked yet. Run `pytm hook link PROJECT` inside a "
            "project directory.[/i]"
        )
        return
    table = Table()
    table.add_column("Path", style="blue")
    table.add_column("Project", style="bold blue")
    for path, project_name in sorted(links.items()):
        table.add_row(path, project_name)
    console.print(table)


@hook.command()
@click.option(
    "--apply",
    "do_apply",
    is_flag=True,
    default=False,
    help="Actually switch project/task. Without this, only prints what would happen.",
)
@click.option(
    "--path",
    default=None,
    help="Directory to resolve. Defaults to the current directory.",
)
def resolve(do_apply, path):
    """
    - resolves the linked project (and git-branch task) for a directory,
      and with --apply switches to it. This is what the shell snippet
      from `pytm hook init` calls on every cd/branch change; it is
      always silent and always exits 0 so it can never break the shell.
    """
    try:
        cwd = hook_handler.normalize(path or os.getcwd())

        if not do_apply:
            state = data_handler.load_data(settings.state_filepath)
            links = state.get("hooks", {}).get("links", {})
            project_name = hook_handler.resolve_project(links, cwd)
            branch = hook_handler.current_branch(cwd)
            if project_name:
                suffix = f", task: {branch}" if branch else ""
                console.print(f"project: {project_name}{suffix}")
            else:
                console.print("No link for this directory.")
            return

        # The whole read-modify-write below is one locked unit: `resolve
        # --apply` runs automatically and frequently (every shell prompt,
        # potentially from several terminals in linked directories at
        # once), so two invocations racing on plain load/mutate/save
        # could otherwise clobber each other's state update. A short
        # timeout means a rare lock collision just skips this tick
        # silently rather than risking a noticeable shell hang.
        with data_handler.locked(settings.state_filepath, timeout=2):
            state = data_handler.load_data(settings.state_filepath)
            links = state.get("hooks", {}).get("links", {})
            project_name = hook_handler.resolve_project(links, cwd)
            if not project_name:
                return
            branch = hook_handler.current_branch(cwd)

            current_project = state.get(settings.CURRENT_PROJECT)
            current_task = state.get(settings.CURRENT_TASK)

            if current_project != project_name:
                if current_project:
                    # Pause every running task in the outgoing project,
                    # not just the one `state` happens to point at —
                    # another task can be left running from an earlier
                    # visit, and leaving it running would silently keep
                    # accruing time while we're elsewhere.
                    data_handler.update(
                        partial(task_handler.pause_all, project_name=current_project)
                    )
                data_handler.update(
                    partial(project_handler.create, project_name=project_name)
                )
                state[settings.CURRENT_PROJECT] = project_name
                state[settings.CURRENT_TASK] = ""
                data_handler.write_unlocked(state, settings.state_filepath)
                current_task = ""

            if branch and branch != current_task:
                # `switch` pauses every running task in `project_name`
                # itself (not just `current_task`) before starting
                # `branch` — covers a task left running in *this*
                # project from an earlier, untracked visit too.
                data_handler.update(
                    partial(
                        task_handler.switch,
                        project_name=project_name,
                        to_task_name=branch,
                    )
                )
                state[settings.CURRENT_TASK] = branch
                data_handler.write_unlocked(state, settings.state_filepath)
    except Exception:
        # An ambient hook must never break the user's shell, no matter
        # what goes wrong (missing git, corrupt state, permissions,
        # lock contention...).
        pass


@hook.command()
@click.argument("shell", type=click.Choice(["bash", "zsh"]))
def init(shell):
    """
    - prints a shell snippet enabling ambient tracking. Add to your rc
      file: eval "$(pytm hook init zsh)"  (or bash).
    """
    click.echo(ZSH_SNIPPET if shell == "zsh" else BASH_SNIPPET)
