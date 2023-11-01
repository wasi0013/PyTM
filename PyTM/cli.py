#!/usr/bin/python
# -*- coding: utf-8 -*-
import click
from PyTM.commands.project import project
from PyTM.commands.task import task
from PyTM import __version__
import os
import datetime
from PyTM.core.data_handler import init_data, load_data, save_data
from PyTM.settings import data_folder, data_filepath, state_filepath, CURRENT_PROJECT, CURRENT_TASK
from PyTM.console import console
from rich.table import Table
from rich.prompt import Prompt
def greet():
    """
    shows Greeting Texts
    :return: None
    """
    console.print("\n\033[1m✨ PyTM ✨\033[0m ")
    console.print(f"CLI V- {__version__}")
    console.print("\033[1m----------------\033[0m")
    console.print("\nTry 'pytm --help' for usage information.\n\n")


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
    console.print("\n[bold green]✨ PyTM ✨")
    console.print(f"version {__version__}")
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
    - initializes the pytm data store.
    """
    console.print("[green on white]Initializing pytm-data.")
    try:
        os.makedirs(data_folder)
        console.print(f"Created data folder: {data_folder}")
    except:
        console.print(f"Data folder already exists: {data_folder}")
    if os.path.exists(data_filepath):
        console.print(f"Data file already exists: {data_filepath}")
    else: 
        init_data(data_filepath)
        console.print(f"Created data file: {data_filepath}")        
        console.print("Done.")
    if os.path.exists(state_filepath):
        console.print(f"State file already exists: {state_filepath}")
    else: 
        init_data(state_filepath, {CURRENT_PROJECT: "", CURRENT_TASK: ""})
        console.print(f"Created state file: {state_filepath}")        
        console.print("Done.")

@click.command()
def show():
    """
    - shows list of projects and status
    """
    data = load_data()
    table = Table()
    table.add_column("Project Name", style='blue bold')
    table.add_column("Created at")
    table.add_column("Status")
    for key, value in data.items():
        table.add_row(key, f'{datetime.datetime.fromisoformat(value['created_at']).strftime("%Y, %B, %d, %H:%M:%S %p")}', value['status'])
    console.print(table)

@click.group()
def config():
    """
    - pytm sub-commands for configuration.
    """
    ...

@config.command()
def user():
    """
    - config default user.
    """
    state = load_data(state_filepath)
    current_user = {}
    if state.get("config"):
        current_user = state.get("config").get("user", {})
        current_user["name"] = Prompt.ask("Name", default=current_user.get("name", ""))
        current_user["email"] = Prompt.ask("Email", default=current_user.get("email", ""))
        current_user["phone"] = Prompt.ask("Phone", default=current_user.get("phone", ""))
        current_user["address"] = Prompt.ask("Address", default=current_user.get("address", ""))
        current_user["website"] = Prompt.ask("Address", default=current_user.get("address", ""))
        current_user["hourly_rate"] = Prompt.ask("Email", default=current_user.get("hourly_rate", ""))
    else:
        state['config'] = dict()
    state['config']['user'] = current_user
    save_data(state, state_filepath)
    console.print("[green] Default user info updated.")
        


cli.add_command(init)
cli.add_command(project)
cli.add_command(task)
cli.add_command(show)
cli.add_command(config)

if __name__ == "__main__":
    cli()
