#!/usr/bin/python
# -*- coding: utf-8 -*-
import click
from click import secho
from PyTM.commands.project import project
from PyTM.commands.task import task
from PyTM import __version__
import os
from PyTM.core.data_handler import init_data
from PyTM.settings import data_folder, data_filepath 

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
    greet()

@click.command()
def init():
    """
    Initialize the pytm data store.
    """
    os.makedirs(data_folder)
    os.chdir(data_folder)
    init_data(data_filepath)

cli.add_command(init)
cli.add_command(project)
cli.add_command(task)


if __name__ == "__main__":
    cli()
