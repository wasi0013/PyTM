from datetime import datetime
import PyTM.settings as settings

def create_project(data, project_name):
    """Create & Start the project
    """
    if data.get(project_name):
        data[project_name]['status'] = settings.STARTED
    else:
        data[project_name] = {
            "tasks": [],
            "created_at": f"{datetime.now()}",
            "status":  settings.STARTED
        }
    return data


def pause_project(data, project_name):
    """Pause the project"""
    if data.get(project_name):
        data[project_name]['status'] = settings.PAUSED
    return data


def finish_project(data, project_name):
    """Finish the project"""
    if data.get(project_name):
        data[project_name]['status'] = settings.FINISHED
    return data



def project_summary(data, project_name):
    """Summarize the project"""
    return data.get(project_name, {})


def project_status(data, project_name):
    """Status of the project"""
    return data.get(project_name, {}).get("status", "")


def abort_project(data, project_name):
    """Abort the project"""
    if data.get(project_name):
        data.get(project_name)['status'] = settings.ABORTED
    return data


def remove_project(data, project_name):
    """Remove the project"""
    if data.get(project_name):
        del data[project_name]
    return data