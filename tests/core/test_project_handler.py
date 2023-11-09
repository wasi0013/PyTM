import datetime

import pytest

from PyTM import settings
from PyTM.core import project_handler

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

    monkeypatch.setattr(project_handler.datetime, "datetime", mydatetime)


def test_create_new_project(test_data, patch_datetime_now):
    project_name = "TEST"
    data = project_handler.create(test_data, project_name)
    assert data[project_name]["status"] == settings.STARTED
    assert data[project_name] == {
        "created_at": f"{TEST_TIME_NOW}",
        "status": settings.STARTED,
        "tasks": {},
    }


def test_start_an_existing_project(test_data, patch_datetime_now):
    project_name = "Test"
    data = project_handler.create(test_data, project_name)
    assert data[project_name]["status"] == settings.STARTED
    assert data[project_name] == {
        "created_at": "2023-11-05 14:55:30.250893",
        "status": settings.STARTED,
        "tasks": {},
    }


def test_pause_an_existing_project(test_data):
    project_name = "Test"
    data = project_handler.pause(test_data, project_name)
    assert data[project_name]["status"] == settings.PAUSED


def test_finish_an_existing_project(test_data):
    project_name = "Test"
    data = project_handler.finish(test_data, project_name)
    assert data[project_name]["status"] == settings.FINISHED


def test_abort_an_existing_project(test_data):
    project_name = "Test"
    data = project_handler.abort(test_data, project_name)
    assert data[project_name]["status"] == settings.ABORTED


def test_summary_of_an_existing_project(test_data):
    project_name = "Test"
    data = project_handler.summary(test_data, project_name)
    assert data == {
        "created_at": "2023-11-05 14:55:30.250893",
        "status": "paused",
        "tasks": {},
    }


def test_status_of_an_existing_project(test_data):
    project_name = "Test"
    status = project_handler.status(test_data, project_name)
    assert status == "paused"


def test_remove_an_existing_project(test_data):
    project_name = "Test"
    data = project_handler.remove(test_data, project_name)
    assert project_name not in data.keys()


def test_rename_an_existing_project(test_data):
    project_name = "Test"
    new_name = "Test_is_renamed"
    data = project_handler.rename(test_data, project_name, new_name)
    assert project_name not in data.keys()
    assert new_name in data.keys()


def test_rename_an_existing_project_new_name_already_exists(test_data):
    project_name = "Test"
    new_name = "Sample"
    data = project_handler.rename(test_data, project_name, new_name)
    assert project_name in data.keys()
    assert new_name in data.keys()


def test_rename_a_non_existing_project(test_data):
    project_name = "TESTDOESNTEXIST"
    new_name = "NEW_PROJECT"
    data = project_handler.rename(test_data, project_name, new_name)
    assert project_name not in data.keys()
    assert new_name not in data.keys()
