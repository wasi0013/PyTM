import click
from functools import partial
from PyTM.core import task_handler
from PyTM.core import data_handler
from PyTM import settings
from PyTM.console import console
import json


@click.group()
def task():
    """
    pytm sub-command for managing tasks.
    """
    pass


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
            console.print("[red bold]No active  task.")
    else:
        console.print("[red bold]No active  project.")


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
@click.argument("task_name")
def start(task_name):
    """
    - starts a new/existing task in current project.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
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
    if state[settings.CURRENT_TASK] == task_name:
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
