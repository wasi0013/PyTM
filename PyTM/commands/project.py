import click
from PyTM.core.project_handler import create_project, pause_project, finish_project, project_summary, project_status, remove_project, abort_project
from functools import partial
from PyTM.core.data_handler import update

@click.group()
def project():
    """
    pytm sub-command for managing projects
    """
    pass


@project.command()
@click.argument("project_name")
def abort(project_name):
    """
    Abort an Ongoing Project with incomplete tasks
    """
    update(partial(abort_project, project_name=project_name))
    click.secho(f"{project_name} aborted.")

@project.command()
@click.argument("project_name")
def finish(project_name):
    """
    Finish a Project by marking all its task completed
    """
    update(partial(finish_project, project_name=project_name))
    click.secho(f"{project_name} finished.")


@project.command()
@click.argument("project_name")
def pause(project_name):
    """
    Pause a Project so, no new task can be added to this project
    """
    update(partial(pause_project, project_name=project_name))
    click.secho(f"{project_name} paused.")


@project.command()
@click.argument("project_name")
def start(project_name):
    """
    Start the Project
    """
    update(partial(create_project, project_name=project_name))
    click.secho(f"{project_name} started.")


@project.command()
@click.argument("project_name")
def remove(project_name):
    """
    Remove a Project and, related task
    """
    update(partial(remove_project, project_name=project_name))
    click.secho(f"{project_name} removed.")

@project.command()
@click.argument("project_name")
def status(project_name):
    """
    Remove a Project and, related task
    """
    click.secho(f"{project_name} status: {project_status(project_name)}")
