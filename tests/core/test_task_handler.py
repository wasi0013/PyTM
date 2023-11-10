import datetime

import pytest

from PyTM import settings
from PyTM.core import task_handler


TEST_TIME_NOW = datetime.datetime(
    2023,
    11,
    9,
)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return TEST_TIME_NOW

    monkeypatch.setattr(task_handler.datetime, "datetime", mydatetime)


def test_calculate_duration():
    date1, date2 = "2023-11-05 14:51:15.498257", "2023-11-03 14:51:15.498257"
    assert task_handler.calculate_duration(date1, date2) == 172800.00


def test_calculate_duration_always_positive():
    date1, date2 = "2023-11-05 14:51:15.498257", "2023-11-03 14:51:15.498257"
    assert task_handler.calculate_duration(date2, date1) == 172800.00


def test_create_task(test_data, patch_datetime_now):
    project_name = "Test"
    task_name = "New Task"
    data = task_handler.create(test_data, project_name, task_name)
    assert task_name in data.get(project_name).get("tasks").keys()
    assert data.get(project_name).get("tasks").get(task_name) == {
        "created_at": f"{TEST_TIME_NOW}",
        "status": "running",
        "duration": 0,
        "since": f"{TEST_TIME_NOW}",
    }


def test_create_task_project_doesnt_exist(test_data):
    project_name = "DOESNTEXIST"
    task_name = "New Task"
    data = task_handler.create(test_data, project_name, task_name)
    assert project_name not in data.keys()
    assert task_name not in data.get(project_name, {}).get("tasks", {}).keys()


def test_pause_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    data = task_handler.pause(test_data, project_name, task_name)
    assert (
        data.get(project_name).get("tasks").get(task_name).get("status")
        == settings.PAUSED
    )


def test_finish_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    data = task_handler.finish(test_data, project_name, task_name)
    assert (
        data.get(project_name).get("tasks").get(task_name).get("status")
        == settings.FINISHED
    )


def test_status_of_a_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    status = task_handler.status(test_data, project_name, task_name)
    assert status == settings.STARTED


def test_abort_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    data = task_handler.abort(test_data, project_name, task_name)
    assert (
        data.get(project_name).get("tasks").get(task_name).get("status")
        == settings.ABORTED
    )


def test_remove_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    data = task_handler.remove(test_data, project_name, task_name)
    assert task_name not in data.get(project_name).get("tasks").keys()


def test_rename_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    new_name = "NEW_NAME"
    data = task_handler.rename(test_data, project_name, task_name, new_name)
    assert task_name not in data.get(project_name).get("tasks").keys()
    assert new_name in data.get(project_name).get("tasks").keys()
