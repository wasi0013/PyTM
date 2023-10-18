from datetime import datetime
from PyTM.settings import PROJECT_ABORTED, PROJECT_FINISHED, PROJECT_STARTED
from PyTM.settings import PROJECT_PAUSED

def create(data, project_name):
    """Create & Start the project
    """
    if data.get(project_name):
        data[project_name]['status'] = PROJECT_STARTED
    else:
        data[project_name] = {
            "tasks": [],
            "created_at": datetime.now(),
            "status":  PROJECT_STARTED
        }
    return data


def pause(data, project_name):
    """Pause the project"""
    if data.get(project_name):
        data[project_name]['status'] = PROJECT_PAUSED
    return data


def finish(data, project_name):
    """Finish the project"""
    if data.get(project_name):
        data[project_name]['status'] = PROJECT_FINISHED
    return data



def summary(data, project_name):
    """Summarize the project"""
    return data.get(project_name, {})


def status(data, project_name):
    """Status of the project"""
    return data.get(project_name, {}).get("status", "")


def abort(data, project_name):
    """Abort the project"""
    if data.get(project_name):
        data.get(project_name)['status'] = PROJECT_ABORTED
    return data


def remove(data, project_name):
    """Remove the project"""
    if data.get(project_name):
        del data[project_name]
    return data