from datetime import datetime

from PyTM import settings


def _calc_duration(date1, date2):
    return (
        datetime.strptime(date1, "%Y-%m-%d %H:%M:%S.%f")
        - datetime.strptime(date2, "%Y-%m-%d %H:%M:%S.%f")
    ).total_seconds()


def create(data, project_name, task_name):
    """Create and/or Start the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.STARTED
            data.get(project_name)["tasks"][task_name]["since"] = f"{datetime.now()}"

        else:
            data.get(project_name)["tasks"][task_name] = {
                "created_at": f"{datetime.now()}",
                "status": settings.STARTED,
                "duration": 0,
                "since": f"{datetime.now()}",
            }

    return data


def pause(data, project_name, task_name):
    """Pause the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.PAUSED
            data.get(project_name)["tasks"][task_name]["duration"] += _calc_duration(
                f"{datetime.now()}", data.get(project_name)["tasks"][task_name]["since"]
            )
            data.get(project_name)["tasks"][task_name]["since"] = ""
    return data


def finish(data, project_name, task_name):
    """Finish the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            data.get(project_name)["tasks"][task_name]["status"] = settings.FINISHED
            data.get(project_name)["tasks"][task_name]["duration"] += _calc_duration(
                f"{datetime.now()}", data.get(project_name)["tasks"][task_name]["since"]
            )
            data.get(project_name)["tasks"][task_name]["since"] = ""
            data.get(project_name)["tasks"][task_name][
                "finished_at"
            ] = f"{datetime.now()}"
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
