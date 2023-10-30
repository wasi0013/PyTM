#!/usr/bin/python
# -*- coding: utf-8 -*-
import click
from click import secho
from PyTM.commands.project import project
from PyTM.commands.task import task
from PyTM import __version__
import os
from PyTM.core.data_handler import init_data
from PyTM.settings import data_folder, data_filepath, state_filepath, CURRENT_PROJECT, CURRENT_TASK

def greet():
    """
    shows Greeting Texts
    :return: None
    """
    secho("\n\033[1m✨ PyTM ✨\033[0m ", fg="green", nl=False)
    secho("CLI V-", nl=False)
    secho(__version__)
    secho("\033[1m----------------\033[0m")
    secho("\nTry 'pytm --help' for usage information.\n\n")


def print_version(ctx, param, value):
    """
    shows version and exits the CLI
    :param ctx:
    :param param:
    :param value:
    :return: None
    """
    if not value:
        return
    secho("\n\033[1m✨ PyTM ✨\033[0m ", fg="green", nl=False)
    secho("version ", nl=False)
    secho(__version__)
    ctx.exit()


@click.group()
@click.option(
    "--version",
    "-v",
    "--v",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Shows version and exit",
)
def cli():
    """
    PyTM - CLI
    docs: https://pytm.rtfd.org
    """
    # greet()

@click.command()
def init():
    """
    Initialize the pytm data store.
    """
    click.secho("Initializing pytm-data.")
    try:
        os.makedirs(data_folder)
        click.secho(f"Created data folder: {data_folder}")
    except:
        click.secho(f"Data folder already exists: {data_folder}", fg="red")
    os.chdir(data_folder)
    if os.path.exists(data_filepath):
        click.secho(f"Data file already exists: {data_filepath}", fg="red")
    else: 
        init_data(data_filepath)
        click.secho(f"Created data file: {data_filepath}")        
        click.secho("Done.")
    if os.path.exists(state_filepath):
        click.secho(f"State file already exists: {state_filepath}", fg="red")
    else: 
        init_data(state_filepath, {CURRENT_PROJECT: "", CURRENT_TASK: ""})
        click.secho(f"Created state file: {state_filepath}")        
        click.secho("Done.")

cli.add_command(init)
cli.add_command(project)
cli.add_command(task)


if __name__ == "__main__":
    cli()
