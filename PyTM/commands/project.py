import click
from PyTM.core.project_handler import create_project, pause_project, finish_project, project_summary, project_status, remove_project, abort_project
from functools import partial
from PyTM.core.data_handler import update, load_data, save_data
import PyTM.settings as settings
import json

@click.group()
def project():
    """
    pytm sub-command for managing projects
    """
    pass

@project.command()
def abort():
    """
    Abort an Ongoing Project with incomplete tasks
    """
    state = load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        update(partial(abort_project, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        save_data(state, settings.state_filepath)
        click.secho(f"{project_name} aborted.")
    else:
        click.secho("No active project.")

@project.command()
def finish():
    """
    Finish current Project
    """
    state = load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        update(partial(finish_project, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        save_data(state, settings.state_filepath)
        click.secho(f"{project_name} finished.")
    else:
        click.secho("No active project.")

@project.command()
def pause():
    """
    Pause a Project
    """
    state = load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        update(partial(pause_project, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        save_data(state, settings.state_filepath)
        click.secho(f"{project_name} paused.")
    else:
        click.secho("No active project.")

@project.command()
@click.argument("project_name")
def start(project_name):
    """
    Start the Project
    """
    update(partial(create_project, project_name=project_name))
    state = load_data(settings.state_filepath)
    state[settings.CURRENT_PROJECT] = project_name
    save_data(state, settings.state_filepath)
    click.secho(f"{project_name} started.")


@project.command()
@click.argument("project_name")
def remove(project_name):
    """
    Remove a Project 
    """
    state = load_data(settings.state_filepath)
    update(partial(remove_project, project_name=project_name))
    if state[settings.CURRENT_PROJECT] == project_name:
        state[settings.CURRENT_PROJECT] = ""
        save_data(state, settings.state_filepath)
    click.secho(f"{project_name} removed.")

@project.command()
@click.argument("project_name")
def status(project_name):
    """
    Status of the Project
    """
    click.secho(f"{project_name} status: {project_status(load_data(), project_name)}")

@project.command()
@click.argument("project_name")
def summary(project_name):
    """
    Summary of the Project
    """
    project_data = project_summary(load_data(), project_name)
    click.secho(f"Project: {project_name}")
    sum_of_durations = [t['duration'] for _, t in project_data]
    m, s = divmod(sum_of_durations, 60)
    h, m = divmod(m, 60)
    duration = f'{h:d}:{m:02d}:{s:02d}'
    click.secho(f"Total duration: {duration}")
    click.secho(f"{json.dumps(project_summary(load_data(), project_name), indent=4)}")