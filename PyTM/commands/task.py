import click
from functools import partial
from PyTM.core import task_handler
from PyTM.core import data_handler
from PyTM import settings
from PyTM.console import console


@click.group(invoke_without_command=True)
@click.pass_context
def task(ctx):
    """
    pytm sub-command for managing tasks.
    """
    # Explicit no-args-is-help handling: Click's own default for this
    # (exit code 0 vs. a `UsageError` with exit code 2) changed between
    # 8.1.x and 8.2+, so relying on it makes `pytm task`'s exit code
    # depend on whatever Click version happens to be installed.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@task.command()
def abort():
    """
    - abort active task.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(
                partial(
                    task_handler.abort, project_name=project_name, task_name=task_name
                )
            )
            state[settings.CURRENT_TASK] = ""
            data_handler.save_data(state, settings.state_filepath)
            console.print(f"Aborted Task [green]{task_name}[/green].")
        else:
            console.print("[red bold]No active task.")
    else:
        console.print("[red bold]No active project.")


@task.command()
def finish():
    """
    - marks active task as finished.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(
                partial(
                    task_handler.finish, project_name=project_name, task_name=task_name
                )
            )
            state[settings.CURRENT_TASK] = ""
            data_handler.save_data(state, settings.state_filepath)
            console.print(f"Finished task: [green]{task_name}[/green].")
        else:
            console.print("[red bold]No active task.")
    else:
        console.print("[red bold]No active project.")


@task.command()
def pause():
    """
    - pauses active task.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(
                partial(
                    task_handler.pause, project_name=project_name, task_name=task_name
                )
            )
            state[settings.CURRENT_TASK] = ""
            data_handler.save_data(state, settings.state_filepath)
            console.print(f"Paused task: [green]{task_name}[/green].")
        else:
            console.print("[red bold]No active task.")
    else:
        console.print("[red bold]No active project.")


@task.command()
@click.argument("task_name", required=False)
def start(task_name):
    """
    - starts a new/existing task in current project.
    """
    data = data_handler.load_data()
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name and data.get(project_name):
        if task_name is None:
            num = len(data.get(project_name).get("tasks", {}).keys())
            while task_name is None or data.get(project_name).get("tasks", {}).get(
                task_name, ""
            ):
                num += 1
                task_name = f"UNTITLED_{num}"
        data_handler.update(
            partial(task_handler.create, project_name=project_name, task_name=task_name)
        )
        state[settings.CURRENT_TASK] = task_name
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"Started task: [green]{task_name}[/green].")
    else:
        console.print("[red bold]No active project.")


@task.command()
@click.argument("project_name")
@click.argument("task_name")
def remove(project_name, task_name):
    """
    - deletes a task from a project.
    """
    state = data_handler.load_data(settings.state_filepath)
    data_handler.update(
        partial(task_handler.remove, project_name=project_name, task_name=task_name)
    )
    if state.get(settings.CURRENT_TASK) == task_name:
        state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
    console.print(f"Removed task [green]{task_name}[/green].")


@task.command()
def status():
    """
    - of the current task (running, stopped, paused, etc).
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)

    if project_name:
        if task_name:
            console.print(
                f"Status of [green]{task_name}[/green]: {task_handler.status(data_handler.load_data(), project_name=project_name, task_name=task_name)}"
            )
        else:
            console.print("[red bold]No active task.")
    else:
        console.print("[red bold]No active project.")


@task.command()
@click.argument("task_name")
def switch(task_name):
    """
    - atomically pauses the active task (if any) and starts/resumes task_name.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if not project_name:
        console.print("[red bold]No active project.")
        return
    data = data_handler.load_data()
    if not data.get(project_name):
        console.print(f"[bold red]Project {project_name} doesn't exist.")
        state[settings.CURRENT_PROJECT] = ""
        data_handler.save_data(state, settings.state_filepath)
        return
    from_task_name = state.get(settings.CURRENT_TASK)
    if from_task_name == task_name:
        console.print(f"[green]{task_name}[/green] is already the active task.")
        return
    data_handler.update(
        partial(
            task_handler.switch,
            project_name=project_name,
            to_task_name=task_name,
        )
    )
    state[settings.CURRENT_TASK] = task_name
    data_handler.save_data(state, settings.state_filepath)
    if from_task_name:
        console.print(
            f"Switched from [green]{from_task_name}[/green] to [green]{task_name}[/green]."
        )
    else:
        console.print(f"Switched to [green]{task_name}[/green].")


@task.command()
@click.argument("task_name")
@click.option(
    "--duration",
    "duration_hours",
    type=float,
    default=None,
    help="Correct this task's total logged duration, in hours. Recorded as a "
    "dated adjustment so `today`/`week` digests stay consistent with the "
    "corrected total instead of drifting from it.",
)
@click.option(
    "--project",
    "project_name",
    default=None,
    help="Project the task belongs to. Defaults to the active project.",
)
def edit(task_name, duration_hours, project_name):
    """
    - manually corrects a task's recorded duration (e.g. after a hook mis-tracked it).
    """
    if duration_hours is None:
        console.print("[red bold]Nothing to edit. Pass --duration HOURS.")
        return
    state = data_handler.load_data(settings.state_filepath)
    project_name = project_name or state.get(settings.CURRENT_PROJECT)
    if not project_name:
        console.print("[red bold]No active project. Pass --project NAME.")
        return
    data = data_handler.load_data()
    if not data.get(project_name):
        console.print(f"[bold red]Project {project_name} doesn't exist.")
        return
    if task_name not in data.get(project_name).get("tasks", {}):
        console.print(f"[bold red]{task_name} doesn't exist.")
        return
    data_handler.update(
        partial(
            task_handler.edit,
            project_name=project_name,
            task_name=task_name,
            duration_hours=duration_hours,
        )
    )
    console.print(
        f"Updated [green]{task_name}[/green] duration to {duration_hours} hours."
    )


@task.command()
@click.argument("task_name")
@click.argument("new_name")
def rename(task_name, new_name):
    """
    - Renames a task of the active project.
    """
    state = data_handler.load_data(settings.state_filepath)
    data = data_handler.load_data()
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        if not data.get(project_name):
            console.print(f"[red bold]Project {project_name} doesn't exist.")
            state[settings.CURRENT_PROJECT] = ""
            data_handler.save_data(state, settings.state_filepath)
            return
        if task_name not in data.get(project_name).get("tasks", []):
            console.print(f"[bold red] {task_name} doesn't exists.")
            return
        if new_name in data.get(project_name).get("tasks", []):
            console.print(f"Task {new_name} already exists. Choose a different name.")
            return
        data_handler.update(
            partial(
                task_handler.rename,
                project_name=project_name,
                task_name=task_name,
                new_name=new_name,
            )
        )
        if state.get(settings.CURRENT_TASK) == task_name:
            state[settings.CURRENT_TASK] = new_name
            data_handler.save_data(state, settings.state_filepath)
        console.print(f"Renamed task: [green]{task_name}[/green] to {new_name}.")
    else:
        console.print("[red bold]No active project.")
