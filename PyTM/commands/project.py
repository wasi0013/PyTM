import click
from PyTM.core.project_handler import create_project, pause_project, finish_project, project_summary, project_status, remove_project, abort_project
from functools import partial
from PyTM.core.data_handler import update, load_data, save_data
import PyTM.settings as settings
from PyTM.console import console
from rich.tree import Tree
from rich.panel import Panel
import json


def _get_duration_str(sum_of_durations):
    m, s = divmod(sum_of_durations, 60)
    duration = ''
    if m > 60:
        h, m = divmod(m, 60)
        if h > 24:
            d, h = divmod(h, 24)
            duration = f'{d:d} days {h:d} hours {m:02d} mins {s:02d} secs'
        else:
            duration = f'{h:d} hours {m:02d} mins {s:02d} secs'
    elif m < 1:
        duration = f'{s:02d} seconds'
    else:
        duration = f'{m:02d} mins {s:02d} secs'
    return duration

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
        console.print(f"[bold blue]{project_name}[/bold blue] aborted.")
    else:
        console.print("No active project.")

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
        console.print(f"[bold blue]{project_name}[/bold blue] finished.")
    else:
        console.print("No active project.")

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
        console.print(f"[bold blue]{project_name}[/bold blue] paused.")
    else:
        console.print("No active project.")

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
    console.print(f"[bold blue]{project_name}[/bold blue] started.")


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
    console.print(f"[bold blue]{project_name}[/bold blue] removed.")

@project.command()
@click.argument("project_name")
def status(project_name):
    """
    Status of the Project
    """
    console.print(f"[bold blue]{project_name}[/bold blue] status: {project_status(load_data(), project_name)}")

@project.command()
@click.argument("project_name")
def summary(project_name):
    """
    Summary of the Project
    """
    project = project_summary(load_data(), project_name)
    project_data = project['tasks']
    tree = Tree(f"[bold blue]{project_name}[/bold blue] ([i]{project["status"]}[/i])")
    duration = 0
    for task, t in project_data.items():
        task_duration = int(round(t['duration']))
        duration += task_duration
        tree.add(f"[green]{task}[/green]: {_get_duration_str(task_duration)} ([i]{t['status']}[/i])")
    console.print(Panel.fit(tree))
    console.print(f"[blue bold]Total time[/blue bold]: {_get_duration_str(duration)}")
    # console.print_json(data=project_summary(load_data(), project_name))