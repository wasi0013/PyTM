import datetime

from PyTM import settings


def calculate_duration(date1, date2):
    return abs(
        (
            datetime.datetime.fromisoformat(date1)
            - datetime.datetime.fromisoformat(date2)
        ).total_seconds()
    )


def create(data, project_name, task_name):
    """Create and/or Start the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.STARTED
            data.get(project_name)["tasks"][task_name][
                "since"
            ] = f"{datetime.datetime.now()}"

        else:
            data.get(project_name)["tasks"][task_name] = {
                "created_at": f"{datetime.datetime.now()}",
                "status": settings.STARTED,
                "duration": 0,
                "since": f"{datetime.datetime.now()}",
            }

    return data


def pause(data, project_name, task_name):
    """Pause the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.PAUSED
            data.get(project_name)["tasks"][task_name][
                "duration"
            ] += calculate_duration(
                f"{datetime.datetime.now()}",
                data.get(project_name)["tasks"][task_name]["since"],
            )
            data.get(project_name)["tasks"][task_name]["since"] = ""
    return data


def finish(data, project_name, task_name):
    """Finish the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.FINISHED
            data.get(project_name)["tasks"][task_name][
                "duration"
            ] += calculate_duration(
                f"{datetime.datetime.now()}",
                data.get(project_name)["tasks"][task_name]["since"],
            )
            data.get(project_name)["tasks"][task_name]["since"] = ""
            data.get(project_name)["tasks"][task_name][
                "finished_at"
            ] = f"{datetime.datetime.now()}"
    return data


def status(data, project_name, task_name):
    """Status of the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            return data.get(project_name)["tasks"][task_name]["status"]


def abort(data, project_name, task_name):
    """Abort the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.ABORTED
    return data


def remove(data, project_name, task_name):
    """Remove the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            del data.get(project_name)["tasks"][task_name]
    return data


def rename(data, project_name, task_name, new_name):
    if data.get(project_name):
        if data.get(project_name).get("tasks"):
            if not data.get(project_name).get("tasks").get(new_name):
                data[project_name]["tasks"][new_name] = data[project_name]["tasks"].pop(
                    task_name
                )
    return data
