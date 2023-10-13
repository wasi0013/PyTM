import click

@click.group()
def task():
    """
    pytm sub-command for managing tasks
    """
    pass


@task.command()
@click.argument("task_name")
def abort(task_name):
    """
    Abort an Ongoing Task
    """
    click.secho("Pause Task " + task_name)


@task.command()
@click.argument("task_name")
def finish(task_name):
    """
    Finish a Task
    """
    click.secho("Finished Task " + task_name)


@task.command()
@click.argument("task_name")
def pause(task_name):
    """
    Pause a Task
    """
    click.secho("Paused Task " + task_name)


@task.command()
@click.argument("project_name")
@click.argument("task_name")
def start(project_name, task_name):
    """
    Start a new Task
    """
    click.secho("Created Task: " + task_name + " for Project: " + project_name)


@task.command()
@click.argument("task_name")
def remove(task_name):
    """
    Remove task
    """
    click.secho("Removed Task " + task_name)
