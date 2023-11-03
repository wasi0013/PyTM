#!/usr/bin/python
# -*- coding: utf-8 -*-
import click
from PyTM import settings
from PyTM.commands.project import project
from PyTM.commands.task import task
from PyTM import __version__
import os
import datetime
from PyTM.core import invoice_handler
from PyTM.core.data_handler import init_data, load_data, save_data
from PyTM.settings import data_folder, data_filepath, state_filepath, CURRENT_PROJECT, CURRENT_TASK
from PyTM.console import console
from rich.table import Table
from rich.prompt import Prompt
from rich.prompt import Confirm
import webbrowser
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
    console.print("[green on white]Initializing pytm-data.\n")
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
    console.print("\n[bold blue i on white]You also might want to run: `pytm config user` to configure default user data.[/bold blue i on white]")

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
    else:
        state['config'] = dict()
    current_user["name"] = Prompt.ask("Name", default=current_user.get("name", ""))
    current_user["email"] = Prompt.ask("Email", default=current_user.get("email", ""))
    current_user["phone"] = Prompt.ask("Phone", default=current_user.get("phone", ""))
    current_user["address"] = Prompt.ask("Address", default=current_user.get("address", ""))
    current_user["website"] = Prompt.ask("Website", default=current_user.get("website", ""))
    current_user["hourly_rate"] = Prompt.ask("Hourly rate in USD", default=current_user.get("hourly_rate", ""))
    state['config']['user'] = current_user
    save_data(state, state_filepath)
    console.print("\n[green]Default user info updated.")

@config.command()
def invoice():
    """
    - configure invoice texts and logo.
    """
    state = load_data(state_filepath)
    invoice = {}
    if state.get("config"):
        invoice = state.get("config").get("invoice", {})
    else:
        state['config'] = dict()
    invoice["title"] = Prompt.ask("Invoice Title", default=invoice.get("title", "Invoice"))
    invoice["logo"] = Prompt.ask("Absolute path of a logo in .png format", default=invoice.get("logo", ""))
    try:
        os.replace(invoice["logo"], os.path.join(data_folder, "invoice-logo.png"))
        invoice["logo"] = os.path.join(data_folder, "invoice-logo.png")
    except Exception as e:
        console.print("[bold red] Error occured while saving the logo.")
        console.print_exception(e)

    invoice["foot_note"] = Prompt.ask("Foot Note?", default=invoice.get("foot_note", "Thank you for your business."))
    invoice['invoice_number'] = Prompt.ask("Default invoice number to start from? (integer)", default="13") 
    state['config']['invoice'] = invoice
    save_data(state, state_filepath)
    console.print("\n[green]invoice texts are updated.")
        
@config.command(name="project")
@click.argument("project_name")
def config_project(project_name):
    """
    - config project meta data.
    """
    data = load_data()
    if data.get(project_name):
        data[project_name]['meta'] = data.get(project_name).get("meta", {})
        data[project_name]['meta']["title"] = Prompt.ask("Project Title", default=data[project_name]['meta'].get("title", ""))
        data[project_name]['meta']["billable"] = Confirm.ask("Billable?", default=data[project_name]['meta'].get("billable", True))
        data[project_name]['meta']["client_name"] = Prompt.ask("Client Name", default=data[project_name]['meta'].get("client_name", ""))
        data[project_name]['meta']["client_email"] = Prompt.ask("Client Email", default=data[project_name]['meta'].get("client_email", ""))
        data[project_name]['meta']["client_phone"] = Prompt.ask("Client Phone", default=data[project_name]['meta'].get("client_phone", ""))
        data[project_name]['meta']["client_address"] = Prompt.ask("Client Address", default=data[project_name]['meta'].get("client_address", ""))
        data[project_name]['meta']["client_website"] = Prompt.ask("Client Website", default=data[project_name]['meta'].get("client_website", ""))
    else:
        console.print(f"[bold red] Project {project_name} doesn't exist.")
    save_data(data)
    console.print("\n[green]Project Meta data updated.")


@click.group()
def invoice():
    """
    - pytm sub-commands for invoice.
    """
    ...
@invoice.command()
@click.argument("project_name")
def auto(project_name):
    """
    - generates invoice for existing projects.
    """
    data = load_data()
    if not data.get(project_name):
        console.print(f"[bold red] {project_name} doesn't exist.")
        return None
    title, logo, foot_note, invoice_number = [''] * 4
    discount = 0
    state = load_data(state_filepath)
    config = state.get("config", {})
    user = config.get("user", {})
    invoice_texts = config.get("invoice", {})
    invoice_number = Prompt.ask("Invoice Number", default=invoice_texts.get("invoice_number", "13"))
    if state.get("config"):
        if state.get("config").get("invoice"):
            if invoice_number == state.get("config").get("invoice").get("invoice_number"):
                try:
                    state["config"]["invoice"]["invoice_number"] = f"{int(state.get("config").get("invoice").get("invoice_number", "13")) + 1}"
                    save_data(state, state_filepath)
                except:
                    pass                
    
    invoice_texts['title'] = Prompt.ask("Invoice Title", default=invoice_texts.get("title", ""))
    invoice_texts['foot_note'] = Prompt.ask("Foot note", default=invoice_texts.get("foot_note", ""))
    invoice_texts['logo'] = Prompt.ask("Logo Absolute path", default=invoice_texts.get("logo", "")) 

    project, user = data[project_name], config.get("user", {})

    if not project['meta']:
        project['meta'] = {}
    project['meta']['title'] = Prompt.ask("Project Name", default=f"{project['meta']['title']}")
    project['created_at'] = Prompt.ask("Project Date (YYYY-MM-DD)", default=f"{project['meta'].get("created_at", datetime.datetime.now())}")
    user["name"] = Prompt.ask("Your Name", default=user.get("name", ""))
    user["email"] = Prompt.ask("Email", default=user.get("email", ""))
    user["phone"] = Prompt.ask("Phone", default=user.get("phone", ""))
    user["address"] = Prompt.ask("Address", default=user.get("address", ""))
    user["website"] = Prompt.ask("Website", default=user.get("website", ""))
    user["hourly_rate"] = Prompt.ask("Hourly rate in USD", default=user.get("hourly_rate", ""))
    project['meta']['client_name'] = Prompt.ask("Bill To Name", default=f"{project['meta'].get('client_name', 'Anonymous Client')}") 
    project['meta']['client_address'] = Prompt.ask("Address(street, state, zip, country)", default=f"{project['meta'].get('client_address', 'earth')}")
    project['meta']['client_phone'] = Prompt.ask("Phone", default=f"{project['meta'].get('client_phone', '')}")
    project['meta']['client_email'] = Prompt.ask("Email", default=f"{project['meta'].get('client_email', '')}")
    project['meta']['client_website'] = Prompt.ask("Website", default=f"{project['meta'].get('client_website', '')}")
    discount = Prompt.ask("Discount?", default="")
    html = invoice_handler.generate(invoice_number, invoice_texts, user, project, discount)
    try:
        os.makedirs(os.path.join(data_folder, "invoices"))
    except:
        pass
    
    html_file = os.path.join(data_folder, "invoices", f"{invoice_texts['title']}.html")
    with open(html_file, "w") as f:
        f.write(html)
    console.print(f"The invoice is available in {html_file}")
    webbrowser.open(f"file:///{html_file}", autoraise=True)
@invoice.command()
def manual():
    """
    - generates invoice Solely based on prompts and config data.
    """
    title, logo, foot_note, invoice_number = [''] * 4
    discount = 0
    state = load_data(state_filepath)
    config = state.get("config", {})
    user = config.get("user", {})
    invoice_texts = config.get("invoice", {})
    invoice_number = Prompt.ask("Invoice Number", default=invoice_texts.get("invoice_number", "13"))
    if state.get("config"):
        if state.get("config").get("invoice"):
            if invoice_number == state.get("config").get("invoice").get("invoice_number"):
                try:
                    state["config"]["invoice"]["invoice_number"] = f"{int(state.get("config").get("invoice").get("invoice_number")) + 1}"
                    save_data(state, state_filepath)
                except:
                    pass                
    
    invoice_texts['title'] = Prompt.ask("Invoice Title", default=invoice_texts.get("title", ""))
    invoice_texts['foot_note'] = Prompt.ask("Foot note", default=invoice_texts.get("foot_note", ""))
    invoice_texts['logo'] = Prompt.ask("Logo Absolute path", default=invoice_texts.get("logo", "")) 

    project, user = {}, config.get("user", {})
    project['meta'] = {}
    project['meta']['title'] = Prompt.ask("Project Name", default="")
    project['created_at'] = Prompt.ask("Project Date (YYYY-MM-DD)", default=f"{datetime.datetime.now()}") 
    user["name"] = Prompt.ask("Your Name", default=user.get("name", ""))
    user["email"] = Prompt.ask("Email", default=user.get("email", ""))
    user["phone"] = Prompt.ask("Phone", default=user.get("phone", ""))
    user["address"] = Prompt.ask("Address", default=user.get("address", ""))
    user["website"] = Prompt.ask("Website", default=user.get("website", ""))
    user["hourly_rate"] = Prompt.ask("Hourly rate in USD", default=user.get("hourly_rate", ""))
    project['meta']['client_name'] = Prompt.ask("Bill To Name", default="Anonymous Client") 
    project['meta']['client_address'] = Prompt.ask("Address(street, state, zip, country)", default="Earth")
    project['meta']['client_phone'] = Prompt.ask("Phone", default="")
    project['meta']['client_email'] = Prompt.ask("Email", default="")
    project['meta']['client_website'] = Prompt.ask("Website", default="")
    tasks = dict()
    number = 1
    while Confirm.ask("Add a task?", default=True):
        task = dict()
        task_name = Prompt.ask("Task name?", default=f"Task {number}")
        if task_name.startswith("Task"): number += 1
        task['description'] = Prompt.ask("Task description?", default="-")
        task['duration'] = Prompt.ask("How many hours of work? (float)", default=0.0)
        task['duration'] = float(task['duration']) * 360
        task['status'] = settings.FINISHED
        tasks[task_name] = task
    project['tasks'] = tasks
    discount = Prompt.ask("Discount?", default="")
    html = invoice_handler.generate(invoice_number, invoice_texts, user, project, discount)
    try:
        os.makedirs(os.path.join(data_folder, "invoices"))
    except:
        pass
    html_file = os.path.join(data_folder,"invoices", f"{invoice_texts['title']}.html")
    with open(html_file, "w") as f:
        f.write(html)
    console.print(f"The invoice is available in {html_file}")
    webbrowser.open(f"file:///{html_file}", autoraise=True)
    






cli.add_command(init)
cli.add_command(project)
cli.add_command(task)
cli.add_command(show)
cli.add_command(config)
cli.add_command(invoice)

if __name__ == "__main__":
    cli()
