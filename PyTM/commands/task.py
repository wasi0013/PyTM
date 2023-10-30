import click
from functools import partial
import PyTM.core.task_handler as task_handler
import PyTM.core.data_handler as data_handler
import PyTM.settings as settings
import json


@click.group()
def task():
    """
    pytm sub-command for managing tasks
    """
    pass


@task.command()
def abort():
    """
    Abort an Ongoing Task
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(partial(task_handler.abort, project_name=project_name, task_name=task_name))
            state[settings.CURRENT_TASK] = ''
            data_handler.save_data(state, settings.state_filepath)
            click.secho("Aborted Task " + task_name)
        else:
            click.secho("No active tasks.")
    else:
        click.secho("No active projects.")


@task.command()
def finish():
    """
    Finish a Task
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(partial(task_handler.finish, project_name=project_name, task_name=task_name))
            state[settings.CURRENT_TASK] = ''
            data_handler.save_data(state, settings.state_filepath)
            click.secho("Finished Task " + task_name)
        else:
            click.secho("No active tasks.")
    else:
        click.secho("No active projects.")


@task.command()
def pause():
    """
    Pause a Task
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    if project_name:
        if task_name:
            data_handler.update(partial(task_handler.pause, project_name=project_name, task_name=task_name))
            state[settings.CURRENT_TASK] = ''
            data_handler.save_data(state, settings.state_filepath)
            click.secho("Paused Task " + task_name)
        else:
            click.secho("No active tasks.")
    else:
        click.secho("No active projects.")


@task.command()
def start(task_name):
    """
    Start a new/existing Task
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(task_handler.create, project_name=project_name, task_name=task_name))
        state[settings.CURRENT_TASK] = task_name
        data_handler.save_data(state, settings.state_filepath)
        click.secho("Started Task " + task_name)
    else:
        click.secho("No active projects.")


@task.command()
@click.argument("project_name")
@click.argument("task_name")
def remove(project_name, task_name):
    """
    Remove a task
    """
    state = data_handler.load_data(settings.state_filepath)
    data_handler.update(partial(task_handler.remove, project_name=project_name, task_name=task_name))
    if state[settings.CURRENT_TASK] == task_name: 
            state[settings.CURRENT_TASK] = ''
            data_handler.save_data(state, settings.state_filepath)
            click.secho("Aborted Task " + task_name)

@task.command()
def status():
    """
    Current task status
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    task_name = state.get(settings.CURRENT_TASK)
    
    if project_name:
        if task_name:
            click.secho(f"Status of {task_name}: {task_handler.status(data_handler.load_data(), project_name=project_name, task_name=task_name)}")
        else:
            click.secho("No active tasks.")
    else:
        click.secho("No active projects.")
