from functools import partial

import click
from rich.panel import Panel
from rich.tree import Tree

from PyTM import settings
from PyTM.console import console
from PyTM.core import task_handler
from PyTM.core import data_handler
from PyTM.core import project_handler


def _get_duration_str(sum_of_durations):
    m, s = divmod(sum_of_durations, 60)
    duration = ""
    if m > 60:
        h, m = divmod(m, 60)
        if h > 24:
            d, h = divmod(h, 24)
            duration = f"{d:d} days {h:d} hours {m:02d} mins {s:02d} secs"
        else:
            duration = f"{h:d} hours {m:02d} mins {s:02d} secs"
    elif m < 1:
        duration = f"{s:02d} seconds"
    else:
        duration = f"{m:02d} mins {s:02d} secs"
    return duration


@click.group()
def project():
    """
    pytm sub-command for managing projects.
    """
    pass


@project.command()
def abort():
    """
    - aborts the current project and task.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.abort, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.abort,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] aborted.")
    else:
        console.print("[bold red]No active project.")


@project.command()
def finish():
    """
    - marks the current project as finished.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.finish, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.finish,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] finished.")
    else:
        console.print("[bold red]No active project.")


@project.command()
def pause():
    """
    - pauses the current project, so new tasks can't be started.
    """
    state = data_handler.load_data(settings.state_filepath)
    project_name = state.get(settings.CURRENT_PROJECT)
    if project_name:
        data_handler.update(partial(project_handler.pause, project_name=project_name))
        state[settings.CURRENT_PROJECT] = ""
        if state[settings.CURRENT_TASK]:
            data_handler.update(
                partial(
                    task_handler.pause,
                    project_name=project_name,
                    task_name=state[settings.CURRENT_TASK],
                )
            )
            state[settings.CURRENT_TASK] = ""
        data_handler.save_data(state, settings.state_filepath)
        console.print(f"[bold blue]{project_name}[/bold blue] paused.")
    else:
        console.print("[bold red]No active project.")


@project.command()
@click.argument("project_name")
def start(project_name):
    """
    - starts an existing project or creates a new project.
    """
    data = data_handler.load_data()
    data_handler.update(partial(project_handler.create, project_name=project_name))
    state = data_handler.load_data(settings.state_filepath)
    state[settings.CURRENT_PROJECT] = project_name
    data_handler.save_data(state, settings.state_filepath)
    console.print(f"[bold blue]{project_name}[/bold blue] started.")
    if project_name not in data.keys():
        console.print(
            f"\n[bold blue i on white]You also might want to run: `pytm config project {project_name}` to configure project meta data.[/bold blue i on white]"
        )


@project.command()
@click.argument("project_name")
def remove(project_name):
    """
    - deletes a project and related tasks.
    """
    state = data_handler.load_data(settings.state_filepath)
    data_handler.update(partial(project_handler.remove, project_name=project_name))
    if state[settings.CURRENT_PROJECT] == project_name:
        state[settings.CURRENT_PROJECT] = ""
        data_handler.save_data(state, settings.state_filepath)
    console.print(f"[bold blue]{project_name}[/bold blue] removed.")


@project.command()
@click.argument("project_name")
def status(project_name):
    """
    - of the project (running, paused, finished, etc).
    """
    console.print(
        f"[bold blue]{project_name}[/bold blue] status: {project_handler.status(data_handler.load_data(), project_name)}"
    )


@project.command()
@click.argument("project_name")
def summary(project_name):
    """
    - shows total time of the project with task and duration.
    """
    project = project_handler.summary(data_handler.load_data(), project_name)
    project_data = project["tasks"]
    tree = Tree(f'[bold blue]{project_name}[/bold blue] ([i]{project["status"]}[/i])')
    duration = 0
    for task, t in project_data.items():
        task_duration = int(round(t["duration"]))
        duration += task_duration
        tree.add(
            f"[green]{task}[/green]: {_get_duration_str(task_duration)} ([i]{t['status']}[/i])"
        )
    console.print(Panel.fit(tree))
    console.print(f"[blue bold]Total time[/blue bold]: {_get_duration_str(duration)}")


@project.command()
@click.argument("project_name")
def json(project_name):
    """
    - shows project data in json format.
    """
    console.print_json(
        data=project_handler.summary(data_handler.load_data(), project_name)
    )
