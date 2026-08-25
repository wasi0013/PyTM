#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import os
import shutil
import webbrowser

import click
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.layout import Layout

from PyTM import __version__, settings
from PyTM.commands.backup import backup
from PyTM.commands.hook import hook
from PyTM.commands.project import project, get_duration_str
from PyTM.commands.task import task
from PyTM.console import console
from PyTM.core import data_handler, digest_handler, invoice_handler


def init_data_store(show_messages=False):
    """
    - initializes the pytm data store.
    """
    messages = []
    messages.append("[green on white]Initializing pytm-data.\n")
    try:
        os.makedirs(settings.data_folder)
        messages.append(f"Created data folder: {settings.data_folder}")
    except Exception as _:
        messages.append(f"Data folder already exists: {settings.data_folder}")
    if not os.path.exists(settings.data_filepath):
        data_handler.init_data(settings.data_filepath)
        messages.append(f"Created data file: {settings.data_filepath}")
    else:
        messages.append(f"Data file already exists: {settings.data_filepath}")

    if not os.path.exists(settings.state_filepath):
        data_handler.init_data(
            settings.state_filepath,
            {settings.CURRENT_PROJECT: "", settings.CURRENT_TASK: ""},
        )
        messages.append(f"Created state file: {settings.state_filepath}")
    else:
        messages.append(f"State file already exists: {settings.state_filepath}")

    if show_messages:
        for message in messages:
            console.print(message)


def prompt_value(value, message, default="", non_interactive=False):
    """
    Returns `value` when it was already supplied (e.g. via a CLI flag).
    Otherwise, in non-interactive mode it falls back to `default` instead
    of blocking on stdin; in interactive mode it prompts as before.
    """
    if value is not None:
        return value
    if non_interactive:
        return default
    return Prompt.ask(message, default=default)


def confirm_value(value, message, default=True, non_interactive=False):
    """
    Confirm.ask counterpart to `prompt_value`.
    """
    if value is not None:
        return value
    if non_interactive:
        return default
    return Confirm.ask(message, default=default)


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
    console.print("docs: https://pytm.rtfd.org")
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
    help="Shows version",
)
def cli():
    """
    docs: https://pytm.rtfd.org\n
    Config:\n
       default user data (optional): `pytm config user`\n
       default invoice texts & logo (optional): `pytm config invoice`
    """
    init_data_store()


@click.command(hidden=True)
def init():
    """
    - initializes & prints data files & folder.
    """
    console.print("[green on white]\nDone.")
    console.print(f"PyTM Data is stored in: {settings.data_folder}")
    console.print(f"Data file: {settings.data_filepath}")
    console.print(f"State file: {settings.state_filepath}")
    console.print(
        "\n[bold blue i on white]You also might want to run: `pytm config user` to configure default user data.[/bold blue i on white]"
    )


@click.command()
def show():
    """
    - shows list of projects and status
    """
    data = data_handler.load_data()
    state = data_handler.load_data(settings.state_filepath)
    table = Table()
    table.add_column("Project Name", style="blue bold")
    table.add_column("Created at")
    table.add_column("Status")
    for key, value in data.items():
        table.add_row(
            key,
            f'{datetime.datetime.fromisoformat(value["created_at"]).strftime("%Y, %B, %d, %H:%M:%S %p")}',
            value["status"],
        )
    message = ""
    if state.get(settings.CURRENT_PROJECT):
        message += f"Active Project: [bold blue]{state[settings.CURRENT_PROJECT]}[/bold blue]\n"
    if state.get(settings.CURRENT_TASK):
        message += f"Active Task: [bold green]{state[settings.CURRENT_TASK]}"
    if message:
        console.print(message)
    console.print(table)


@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """
    - pytm sub-commands for configuration.
    """
    # Explicit no-args-is-help handling: Click's own default for this
    # (exit code 0 vs. a `UsageError` with exit code 2) changed between
    # 8.1.x and 8.2+, so relying on it makes `pytm config`'s exit code
    # depend on whatever Click version happens to be installed.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@config.command()
@click.option("--name", default=None, help="Your name.")
@click.option("--email", default=None, help="Your email.")
@click.option("--phone", default=None, help="Your phone number.")
@click.option("--address", default=None, help="Your address.")
@click.option("--website", default=None, help="Your website.")
@click.option(
    "--hourly-rate", "hourly_rate", default=None, help="Your hourly rate in USD."
)
@click.option(
    "--week-start",
    "week_start",
    default=None,
    type=click.Choice(list(settings.WEEKDAYS), case_sensitive=False),
    help="Day `pytm week` treats as the start of the week.",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Never prompt; use the flags above (or the existing/blank value) for anything not passed.",
)
def user(
    name, email, phone, address, website, hourly_rate, week_start, non_interactive
):
    """
    - config default user.
    """
    state = data_handler.load_data(settings.state_filepath)
    current_user = {}
    if state.get("config"):
        current_user = state.get("config").get("user", {})
    else:
        state["config"] = dict()
    current_user["name"] = prompt_value(
        name, "Name", current_user.get("name", ""), non_interactive
    )
    current_user["email"] = prompt_value(
        email, "Email", current_user.get("email", ""), non_interactive
    )
    current_user["phone"] = prompt_value(
        phone, "Phone", current_user.get("phone", ""), non_interactive
    )
    current_user["address"] = prompt_value(
        address, "Address", current_user.get("address", ""), non_interactive
    )
    current_user["website"] = prompt_value(
        website, "Website", current_user.get("website", ""), non_interactive
    )
    current_user["hourly_rate"] = prompt_value(
        hourly_rate,
        "Hourly rate in USD",
        current_user.get("hourly_rate", ""),
        non_interactive,
    )
    default_week_start = current_user.get("week_start", settings.DEFAULT_WEEK_START)
    if week_start is not None:
        current_user["week_start"] = week_start
    elif non_interactive:
        current_user["week_start"] = default_week_start
    else:
        current_user["week_start"] = Prompt.ask(
            "Week start day",
            choices=list(settings.WEEKDAYS),
            default=default_week_start,
        )
    state["config"]["user"] = current_user
    data_handler.save_data(state, settings.state_filepath)
    console.print("\n[green]Default user info updated.")


@config.command("invoice")
@click.option("--title", default=None, help="Invoice title.")
@click.option("--logo", default=None, help="Absolute path of a logo in .png format.")
@click.option("--foot-note", "foot_note", default=None, help="Invoice foot note.")
@click.option(
    "--invoice-number",
    "invoice_number",
    default=None,
    help="Default invoice number to start from.",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Never prompt; use the flags above (or the existing/default value) for anything not passed.",
)
def config_invoice(title, logo, foot_note, invoice_number, non_interactive):
    """
    - configure invoice texts and logo.
    """
    state = data_handler.load_data(settings.state_filepath)
    invoice = {}
    if state.get("config"):
        invoice = state.get("config").get("invoice", {})
    else:
        state["config"] = dict()
    invoice["title"] = prompt_value(
        title, "Invoice Title", invoice.get("title", "Invoice"), non_interactive
    )
    invoice["logo"] = prompt_value(
        logo,
        "Absolute path of a logo in .png format",
        invoice.get("logo", ""),
        non_interactive,
    )
    if invoice["logo"]:
        try:
            shutil.copy2(
                invoice["logo"], os.path.join(settings.data_folder, "invoice-logo.png")
            )
            invoice["logo"] = os.path.join(settings.data_folder, "invoice-logo.png")
        except Exception as _:
            console.print("[bold red] Error occured while saving the logo.")
            console.print_exception()

    invoice["foot_note"] = prompt_value(
        foot_note,
        "Foot Note?",
        invoice.get("foot_note", "Thank you for your business."),
        non_interactive,
    )
    invoice["invoice_number"] = prompt_value(
        invoice_number,
        "Default invoice number to start from? (integer)",
        "13",
        non_interactive,
    )
    state["config"]["invoice"] = invoice
    data_handler.save_data(state, settings.state_filepath)
    console.print("\n[green]invoice texts are updated.")


@config.command(name="project")
@click.argument("project_name")
@click.option("--title", default=None, help="Project title.")
@click.option(
    "--billable/--not-billable",
    "billable",
    default=None,
    help="Whether the project is billable.",
)
@click.option("--client-name", "client_name", default=None, help="Client name.")
@click.option("--client-email", "client_email", default=None, help="Client email.")
@click.option("--client-phone", "client_phone", default=None, help="Client phone.")
@click.option(
    "--client-address", "client_address", default=None, help="Client address."
)
@click.option(
    "--client-website", "client_website", default=None, help="Client website."
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Never prompt; use the flags above (or the existing/default value) for anything not passed.",
)
def config_project(
    project_name,
    title,
    billable,
    client_name,
    client_email,
    client_phone,
    client_address,
    client_website,
    non_interactive,
):
    """
    - config project meta data.
    """
    data = data_handler.load_data()
    if data.get(project_name):
        meta = data.get(project_name).get("meta", {})
        meta["title"] = prompt_value(
            title, "Project Title", meta.get("title", ""), non_interactive
        )
        meta["billable"] = confirm_value(
            billable, "Billable?", meta.get("billable", True), non_interactive
        )
        meta["client_name"] = prompt_value(
            client_name, "Client Name", meta.get("client_name", ""), non_interactive
        )
        meta["client_email"] = prompt_value(
            client_email, "Client Email", meta.get("client_email", ""), non_interactive
        )
        meta["client_phone"] = prompt_value(
            client_phone, "Client Phone", meta.get("client_phone", ""), non_interactive
        )
        meta["client_address"] = prompt_value(
            client_address,
            "Client Address",
            meta.get("client_address", ""),
            non_interactive,
        )
        meta["client_website"] = prompt_value(
            client_website,
            "Client Website",
            meta.get("client_website", ""),
            non_interactive,
        )
        data[project_name]["meta"] = meta
    else:
        console.print(f"[bold red] Project {project_name} doesn't exist.")
    data_handler.save_data(data)
    console.print("\n[green]Project Meta data updated.")


@click.group(invoke_without_command=True)
@click.pass_context
def invoice(ctx):
    """
    - pytm sub-commands for invoice.
    """
    # Explicit no-args-is-help handling: Click's own default for this
    # (exit code 0 vs. a `UsageError` with exit code 2) changed between
    # 8.1.x and 8.2+, so relying on it makes `pytm invoice`'s exit code
    # depend on whatever Click version happens to be installed.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@invoice.command()
@click.argument("project_name")
@click.option("--invoice-number", "invoice_number", default=None)
@click.option("--title", default=None, help="Invoice title.")
@click.option("--foot-note", "foot_note", default=None)
@click.option("--logo", default=None)
@click.option("--project-title", "project_title", default=None)
@click.option(
    "--project-date", "project_date", default=None, help="Project date (YYYY-MM-DD)."
)
@click.option("--user-name", "user_name", default=None)
@click.option("--user-email", "user_email", default=None)
@click.option("--user-phone", "user_phone", default=None)
@click.option("--user-address", "user_address", default=None)
@click.option("--user-website", "user_website", default=None)
@click.option("--hourly-rate", "hourly_rate", default=None)
@click.option("--client-name", "client_name", default=None)
@click.option("--client-address", "client_address", default=None)
@click.option("--client-phone", "client_phone", default=None)
@click.option("--client-email", "client_email", default=None)
@click.option("--client-website", "client_website", default=None)
@click.option("--discount", default=None)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Never prompt; use the flags above (or the existing/default value) for anything not passed.",
)
def auto(
    project_name,
    invoice_number,
    title,
    foot_note,
    logo,
    project_title,
    project_date,
    user_name,
    user_email,
    user_phone,
    user_address,
    user_website,
    hourly_rate,
    client_name,
    client_address,
    client_phone,
    client_email,
    client_website,
    discount,
    non_interactive,
):
    """
    - generates invoice for existing projects.
    """
    data = data_handler.load_data()
    if not data.get(project_name):
        console.print(f"[bold red] {project_name} doesn't exist.")
        return None
    state = data_handler.load_data(settings.state_filepath)
    config = state.get("config", {})
    user = config.get("user", {})
    invoice_texts = config.get("invoice", {})
    invoice_number = prompt_value(
        invoice_number,
        "Invoice Number",
        invoice_texts.get("invoice_number", "13"),
        non_interactive,
    )
    if state.get("config"):
        if state.get("config").get("invoice"):
            if invoice_number == state.get("config").get("invoice").get(
                "invoice_number"
            ):
                try:
                    state["config"]["invoice"][
                        "invoice_number"
                    ] = f'{int(state.get("config").get("invoice").get("invoice_number", "13")) + 1}'
                    data_handler.save_data(state, settings.state_filepath)
                except Exception as _:
                    pass

    invoice_texts["title"] = prompt_value(
        title, "Invoice Title", invoice_texts.get("title", ""), non_interactive
    )
    invoice_texts["foot_note"] = prompt_value(
        foot_note, "Foot note", invoice_texts.get("foot_note", ""), non_interactive
    )
    invoice_texts["logo"] = prompt_value(
        logo, "Logo Absolute path", invoice_texts.get("logo", ""), non_interactive
    )

    project, user = data[project_name], config.get("user", {})

    if not project.get("meta"):
        project["meta"] = {}
    project["meta"]["title"] = prompt_value(
        project_title, "Project Name", project["meta"].get("title", ""), non_interactive
    )
    project["created_at"] = prompt_value(
        project_date,
        "Project Date (YYYY-MM-DD)",
        f'{project.get("created_at", datetime.datetime.now())}',
        non_interactive,
    )
    user["name"] = prompt_value(
        user_name, "Your Name", user.get("name", ""), non_interactive
    )
    user["email"] = prompt_value(
        user_email, "Email", user.get("email", ""), non_interactive
    )
    user["phone"] = prompt_value(
        user_phone, "Phone", user.get("phone", ""), non_interactive
    )
    user["address"] = prompt_value(
        user_address, "Address", user.get("address", ""), non_interactive
    )
    user["website"] = prompt_value(
        user_website, "Website", user.get("website", ""), non_interactive
    )
    user["hourly_rate"] = prompt_value(
        hourly_rate,
        "Hourly rate in USD",
        user.get("hourly_rate", ""),
        non_interactive,
    )
    project["meta"]["client_name"] = prompt_value(
        client_name,
        "Bill To Name",
        project["meta"].get("client_name", "Anonymous Client"),
        non_interactive,
    )
    project["meta"]["client_address"] = prompt_value(
        client_address,
        "Address(street, state, zip, country)",
        project["meta"].get("client_address", "earth"),
        non_interactive,
    )
    project["meta"]["client_phone"] = prompt_value(
        client_phone,
        "Phone",
        project["meta"].get("client_phone", ""),
        non_interactive,
    )
    project["meta"]["client_email"] = prompt_value(
        client_email,
        "Email",
        project["meta"].get("client_email", ""),
        non_interactive,
    )
    project["meta"]["client_website"] = prompt_value(
        client_website,
        "Website",
        project["meta"].get("client_website", ""),
        non_interactive,
    )
    discount = prompt_value(discount, "Discount?", "", non_interactive)
    html = invoice_handler.generate(
        invoice_number, invoice_texts, user, project, discount
    )
    try:
        os.makedirs(os.path.join(settings.data_folder, "invoices"))
    except Exception as _:
        pass

    html_file = os.path.join(
        settings.data_folder, "invoices", f"{invoice_texts['title']}.html"
    )
    with open(html_file, "w") as f:
        f.write(html)
    console.print(f"The invoice is available in {html_file}")
    if not non_interactive:
        webbrowser.open(f"file:///{html_file}", autoraise=True)


@invoice.command()
@click.option("--invoice-number", "invoice_number", default=None)
@click.option("--title", default=None, help="Invoice title.")
@click.option("--foot-note", "foot_note", default=None)
@click.option("--logo", default=None)
@click.option("--project-title", "project_title", default=None)
@click.option(
    "--project-date", "project_date", default=None, help="Project date (YYYY-MM-DD)."
)
@click.option("--user-name", "user_name", default=None)
@click.option("--user-email", "user_email", default=None)
@click.option("--user-phone", "user_phone", default=None)
@click.option("--user-address", "user_address", default=None)
@click.option("--user-website", "user_website", default=None)
@click.option("--hourly-rate", "hourly_rate", default=None)
@click.option("--client-name", "client_name", default=None)
@click.option("--client-address", "client_address", default=None)
@click.option("--client-phone", "client_phone", default=None)
@click.option("--client-email", "client_email", default=None)
@click.option("--client-website", "client_website", default=None)
@click.option("--discount", default=None)
@click.option(
    "--task",
    "tasks",
    multiple=True,
    help='Add a billable task as "NAME:HOURS[:DESCRIPTION]". Repeatable. '
    "In --non-interactive mode this is the only way to add tasks.",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Never prompt; use the flags above and --task entries only.",
)
def manual(
    invoice_number,
    title,
    foot_note,
    logo,
    project_title,
    project_date,
    user_name,
    user_email,
    user_phone,
    user_address,
    user_website,
    hourly_rate,
    client_name,
    client_address,
    client_phone,
    client_email,
    client_website,
    discount,
    tasks,
    non_interactive,
):
    """
    - generates invoice Solely based on prompts and config data.
    """
    state = data_handler.load_data(settings.state_filepath)
    config = state.get("config", {})
    user = config.get("user", {})
    invoice_texts = config.get("invoice", {})
    invoice_number = prompt_value(
        invoice_number,
        "Invoice Number",
        invoice_texts.get("invoice_number", "13"),
        non_interactive,
    )
    if state.get("config"):
        if state.get("config").get("invoice"):
            if invoice_number == state.get("config").get("invoice").get(
                "invoice_number"
            ):
                try:
                    state["config"]["invoice"][
                        "invoice_number"
                    ] = f'{int(state.get("config").get("invoice").get("invoice_number")) + 1}'
                    data_handler.save_data(state, settings.state_filepath)
                except Exception as _:
                    pass

    invoice_texts["title"] = prompt_value(
        title, "Invoice Title", invoice_texts.get("title", ""), non_interactive
    )
    invoice_texts["foot_note"] = prompt_value(
        foot_note, "Foot note", invoice_texts.get("foot_note", ""), non_interactive
    )
    invoice_texts["logo"] = prompt_value(
        logo, "Logo Absolute path", invoice_texts.get("logo", ""), non_interactive
    )

    project, user = {}, config.get("user", {})
    project["meta"] = {}
    project["meta"]["title"] = prompt_value(
        project_title, "Project Name", "", non_interactive
    )
    project["created_at"] = prompt_value(
        project_date,
        "Project Date (YYYY-MM-DD)",
        f"{datetime.datetime.now()}",
        non_interactive,
    )
    user["name"] = prompt_value(
        user_name, "Your Name", user.get("name", ""), non_interactive
    )
    user["email"] = prompt_value(
        user_email, "Email", user.get("email", ""), non_interactive
    )
    user["phone"] = prompt_value(
        user_phone, "Phone", user.get("phone", ""), non_interactive
    )
    user["address"] = prompt_value(
        user_address, "Address", user.get("address", ""), non_interactive
    )
    user["website"] = prompt_value(
        user_website, "Website", user.get("website", ""), non_interactive
    )
    user["hourly_rate"] = prompt_value(
        hourly_rate,
        "Hourly rate in USD",
        user.get("hourly_rate", ""),
        non_interactive,
    )
    project["meta"]["client_name"] = prompt_value(
        client_name, "Bill To Name", "Anonymous Client", non_interactive
    )
    project["meta"]["client_address"] = prompt_value(
        client_address,
        "Address(street, state, zip, country)",
        "Earth",
        non_interactive,
    )
    project["meta"]["client_phone"] = prompt_value(
        client_phone, "Phone", "", non_interactive
    )
    project["meta"]["client_email"] = prompt_value(
        client_email, "Email", "", non_interactive
    )
    project["meta"]["client_website"] = prompt_value(
        client_website, "Website", "", non_interactive
    )

    tasks_dict = dict()
    for i, entry in enumerate(tasks, start=1):
        parts = entry.split(":", 2)
        task_name = parts[0] or f"Task {i}"
        hours = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
        description = parts[2] if len(parts) > 2 else "-"
        tasks_dict[task_name] = {
            "description": description,
            "duration": hours * 3600,
            "status": settings.FINISHED,
        }
    if not non_interactive:
        number = 1
        while Confirm.ask("Add a task?", default=True):
            task = dict()
            task_name = Prompt.ask("Task name?", default=f"Task {number}")
            if task_name.startswith("Task"):
                number += 1
            task["description"] = Prompt.ask("Task description?", default="-")
            task["duration"] = Prompt.ask(
                "How many hours of work? (float)", default=0.0
            )
            task["duration"] = float(task["duration"]) * 3600
            task["status"] = settings.FINISHED
            tasks_dict[task_name] = task
    project["tasks"] = tasks_dict
    discount = prompt_value(discount, "Discount?", "", non_interactive)
    html = invoice_handler.generate(
        invoice_number, invoice_texts, user, project, discount
    )
    try:
        os.makedirs(os.path.join(settings.data_folder, "invoices"))
    except Exception as _:
        pass
    html_file = os.path.join(
        settings.data_folder, "invoices", f"{invoice_texts['title']}.html"
    )
    with open(html_file, "w") as f:
        f.write(html)
    console.print(f"The invoice is available in {html_file}")
    if not non_interactive:
        webbrowser.open(f"file:///{html_file}", autoraise=True)


@click.command()
def summary():
    """
    - shows summary of all projects.
    """
    data = data_handler.load_data()
    layout = Layout()

    count = 0
    left, right = [], []
    for project_name in data:
        project_data = data.get(project_name, {}).get("tasks", {})
        tree = Tree(
            f'[bold blue]{project_name}[/bold blue] ([i]{data.get(project_name, {})["status"]}[/i])'
        )
        if project_data == {}:
            tree.add("[red] No tasks yet. [/red]")
            right.append(Panel(tree, title=f"{project_name}"))
            continue
        duration = 0
        for task_name, t in project_data.items():
            task_duration = int(round(t["duration"]))
            duration += task_duration
            tree.add(
                f"[green]{task_name}[/green]: {get_duration_str(task_duration)} ([i]{t['status']}[/i])"
            )
        left.append(
            Panel(
                tree,
                title=f"{project_name}",
                subtitle=f"[blue bold]Total time[/blue bold]: {get_duration_str(duration)}",
                expand=False,
            )
        )
        count += 1
    layout.split_row(  # *p)
        Layout(name="left", size=45),
        Layout(name="right", size=55),
    )
    layout["left"].split_column(*left)
    layout["right"].split_column(*right)
    console.print(layout)


def _configured_week_start():
    state = data_handler.load_data(settings.state_filepath)
    return (
        state.get("config", {})
        .get("user", {})
        .get("week_start", settings.DEFAULT_WEEK_START)
    )


def _format_signed_duration(seconds):
    """
    `get_duration_str` assumes non-negative elapsed time, true for every
    other caller (a task's total time worked can't be negative). Digest
    entries can go negative, though: a `task edit` correction can
    outweigh the other time logged that day. Feeding a negative number
    straight into `get_duration_str` silently mangles it instead of
    raising (e.g. `divmod(-10800, 60)` renders as "00 seconds"), so
    negative values are formatted as a sign plus the magnitude instead.
    """
    seconds = int(round(seconds))
    if seconds < 0:
        return f"-{get_duration_str(-seconds)}"
    return get_duration_str(seconds)


def _print_digest(title, window_start, window_end):
    breakdown = digest_handler.collect(
        data_handler.load_data(), window_start, window_end
    )
    console.print(
        f"[bold blue]{title}[/bold blue] "
        f"({window_start:%Y-%m-%d %H:%M} through now)"
    )
    if not breakdown:
        console.print("[i]Nothing logged in this window.[/i]")
        return

    total = 0
    has_legacy = False
    for project_name, tasks in breakdown.items():
        tree = Tree(f"[bold blue]{project_name}[/bold blue]")
        project_total = 0
        for task_name, info in tasks.items():
            project_total += info["seconds"]
            total += info["seconds"]
            has_legacy = has_legacy or info["legacy"]
            suffix = " [i](legacy, approximate)[/i]" if info["legacy"] else ""
            tree.add(
                f"[green]{task_name}[/green]: "
                f"{_format_signed_duration(info['seconds'])}{suffix}"
            )
        console.print(
            Panel(
                tree,
                title=project_name,
                subtitle=f"[blue bold]Subtotal[/blue bold]: "
                f"{_format_signed_duration(project_total)}",
                expand=False,
            )
        )
    console.print(f"[bold blue]Total[/bold blue]: {_format_signed_duration(total)}")
    if has_legacy:
        console.print(
            "[i]Entries marked (legacy, approximate) predate per-session "
            "tracking; they're bucketed on their finish date rather than "
            "time-weighted within the window.[/i]"
        )


@click.command()
def today():
    """
    - shows time logged today, across all projects.
    """
    start, end = digest_handler.day_window()
    _print_digest("Today", start, end)


@click.command()
def week():
    """
    - shows time logged this week, across all projects.
    """
    start, end = digest_handler.week_window(_configured_week_start())
    _print_digest("This week", start, end)


cli.add_command(init)
cli.add_command(project)
cli.add_command(task)
cli.add_command(hook)
cli.add_command(backup)
cli.add_command(show)
cli.add_command(config)
cli.add_command(invoice)
cli.add_command(summary)
cli.add_command(today)
cli.add_command(week)

if __name__ == "__main__":
    cli()
