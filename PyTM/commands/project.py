import click


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
    click.secho("Pause Project "+project_name)


@project.command()
@click.argument("project_name")
def finish(project_name):
    """
    Finish a Project by marking all its task completed
    """
    click.secho("Finished Project "+project_name)


@project.command()
@click.argument("project_name")
def pause(project_name):
    """
    Pause a Project so, no new task can be added to this project
    """
    click.secho("Paused Project "+project_name)


@project.command()
@click.argument("project_name")
def start(project_name):
    """
    Start the Project
    """
    click.secho("Created Project "+project_name)


@project.command()
@click.argument("project_name")
def remove(project_name):
    """
    Remove a Project and, related task
    """
    click.secho("Removed Project "+project_name)
