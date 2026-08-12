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
        "sessions": [{"start": f"{TEST_TIME_NOW}", "end": None}],
    }


def test_create_task_already_running_is_a_noop(test_data, patch_datetime_now):
    """
    Regression: re-starting an already-running task used to reset `since`
    to now without first folding the elapsed time into `duration`,
    silently dropping it. Ambient hooks that redundantly call
    start/switch on the active task must be safe to call repeatedly.
    """
    project_name = "BEST"
    task_name = "UNTITLED_1"  # already running per test_data, since != now
    original_since = test_data[project_name]["tasks"][task_name]["since"]
    data = task_handler.create(test_data, project_name, task_name)
    assert data[project_name]["tasks"][task_name]["since"] == original_since
    assert "sessions" not in data[project_name]["tasks"][task_name]  # untouched


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


def test_pause_already_paused_task_does_not_crash(test_data):
    """
    Regression: pause() did `duration += calculate_duration(now, since)`
    unconditionally, which raised `ValueError: Invalid isoformat string`
    once `since` had already been cleared to "" by a prior pause. Ambient
    cd/branch hooks will call pause redundantly, so this must be a no-op.
    """
    project_name = "BEST"
    task_name = "UNTITLED_1"
    once = task_handler.pause(test_data, project_name, task_name)
    duration_after_first_pause = once[project_name]["tasks"][task_name]["duration"]
    twice = task_handler.pause(once, project_name, task_name)
    task = twice[project_name]["tasks"][task_name]
    assert task["status"] == settings.PAUSED
    assert task["duration"] == duration_after_first_pause  # unchanged, not double-added


def test_pause_finished_task_does_not_resurrect_it(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    finished = task_handler.finish(test_data, project_name, task_name)
    paused = task_handler.pause(finished, project_name, task_name)
    assert paused[project_name]["tasks"][task_name]["status"] == settings.FINISHED


def test_finish_task(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    data = task_handler.finish(test_data, project_name, task_name)
    assert (
        data.get(project_name).get("tasks").get(task_name).get("status")
        == settings.FINISHED
    )


def test_finish_already_finished_task_does_not_crash_or_drift(test_data):
    """
    Regression: same `since == ""` crash as double-pause, but via finish.
    Also asserts the original `finished_at` isn't clobbered by a second
    call.
    """
    project_name = "BEST"
    task_name = "UNTITLED_1"
    once = task_handler.finish(test_data, project_name, task_name)
    finished_at = once[project_name]["tasks"][task_name]["finished_at"]
    twice = task_handler.finish(once, project_name, task_name)
    task = twice[project_name]["tasks"][task_name]
    assert task["status"] == settings.FINISHED
    assert task["finished_at"] == finished_at


def test_finish_paused_task_does_not_crash(test_data):
    project_name = "BEST"
    task_name = "UNTITLED_1"
    paused = task_handler.pause(test_data, project_name, task_name)
    finished = task_handler.finish(paused, project_name, task_name)
    assert finished[project_name]["tasks"][task_name]["status"] == settings.FINISHED


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


def test_abort_running_task_accumulates_duration_and_closes_session(
    test_data, patch_datetime_now
):
    """
    Regression: abort() used to flip status to ABORTED without folding
    the time since `since` into `duration` or clearing `since`/closing
    the open session, silently losing whatever time was logged before
    the abort and leaving a dangling open session.
    """
    project_name = "BEST"
    task_name = "UNTITLED_1"
    task = test_data[project_name]["tasks"][task_name]
    task["sessions"] = [{"start": task["since"], "end": None}]
    duration_before = task["duration"]
    data = task_handler.abort(test_data, project_name, task_name)
    result = data[project_name]["tasks"][task_name]
    assert result["status"] == settings.ABORTED
    assert result["duration"] > duration_before
    assert result["since"] == ""
    assert result["sessions"][-1]["end"] == f"{TEST_TIME_NOW}"


def test_abort_already_aborted_task_does_not_crash(test_data):
    once = task_handler.abort(test_data, "BEST", "UNTITLED_1")
    twice = task_handler.abort(once, "BEST", "UNTITLED_1")
    assert twice["BEST"]["tasks"]["UNTITLED_1"]["status"] == settings.ABORTED


def test_switch_pauses_running_task_and_starts_to_task(test_data, patch_datetime_now):
    project_name = "BEST"
    data = task_handler.switch(test_data, project_name, "TODO")
    tasks = data[project_name]["tasks"]
    assert tasks["UNTITLED_1"]["status"] == settings.PAUSED
    assert tasks["TODO"]["status"] == settings.STARTED


def test_switch_pauses_every_running_task_not_just_the_recorded_one(
    test_data, patch_datetime_now
):
    """
    Regression: `switch` used to only pause a single caller-supplied
    "from" task. A task left running that the caller didn't know about
    (started manually, or by an earlier hook resolve that didn't get to
    update state) would keep running alongside the new one — two tasks
    simultaneously `STARTED` in the same project. `switch` now pauses
    every running task in the project via `pause_all`, regardless of
    which one (if any) the caller thinks is active.
    """
    project_name = "BEST"
    # A second task, unrelated to whatever the caller thinks is active.
    task_handler.create(test_data, project_name, "second-running-task")
    data = task_handler.switch(test_data, project_name, "TODO")
    tasks = data[project_name]["tasks"]
    assert tasks["UNTITLED_1"]["status"] == settings.PAUSED
    assert tasks["second-running-task"]["status"] == settings.PAUSED
    assert tasks["TODO"]["status"] == settings.STARTED


def test_switch_to_the_already_running_task_still_pauses_and_resumes_it(
    test_data, patch_datetime_now
):
    """
    Not a true no-op: `switch` always pauses everything running in the
    project first (folding elapsed time into `duration` and closing the
    session), then resumes the target — even when the target was already
    the one running. Neither real caller (the `task switch` CLI command,
    the hook) actually calls `switch` in this situation — both skip the
    call entirely when the target is already active — so this documents
    the behavior for any other caller rather than testing a hot path.
    """
    project_name = "BEST"
    original_since = test_data[project_name]["tasks"]["UNTITLED_1"]["since"]
    data = task_handler.switch(test_data, project_name, "UNTITLED_1")
    task = data[project_name]["tasks"]["UNTITLED_1"]
    assert task["status"] == settings.STARTED
    assert task["since"] != original_since  # paused-then-resumed, not skipped
    assert task["duration"] > 0  # the pause folded elapsed time in


def test_switch_with_nothing_running_just_starts_to_task(test_data, patch_datetime_now):
    project_name = "Test"  # no tasks at all in this fixture project
    data = task_handler.switch(test_data, project_name, "TODO")
    assert data[project_name]["tasks"]["TODO"]["status"] == settings.STARTED


def test_edit_sets_duration_and_records_adjustment_session(
    test_data, patch_datetime_now
):
    project_name = "BEST"
    task_name = "TODO"
    original_duration = test_data[project_name]["tasks"][task_name]["duration"]
    data = task_handler.edit(test_data, project_name, task_name, duration_hours=2.5)
    task = data[project_name]["tasks"][task_name]
    assert task["duration"] == 2.5 * 3600
    assert task["sessions"][-1]["delta"] == 2.5 * 3600 - original_duration
    assert task["sessions"][-1]["start"] == task["sessions"][-1]["end"]


def test_edit_on_legacy_task_preserves_its_original_digest_attribution():
    """
    Regression: a legacy task (no `sessions` yet) is digested via
    `digest_handler`'s finished_at-bucketed fallback, which attributes
    its *full* `duration` to the day it was finished. Before this fix,
    `edit()` appended only the delta as a session, which flips the task
    onto the session-based digest path — where only that delta is
    visible — silently dropping the task's original duration from every
    digest showing the day it was finished. The finish-day total must
    stay what it was; the correction itself shows up on the day it was
    made (today), same as a correction to a non-legacy task would.
    """
    from PyTM.core import digest_handler

    project_name = "BEST"
    task_name = "TODO"  # legacy in the fixture: no `sessions`, has `finished_at`
    finished_at = datetime.datetime.fromisoformat(
        "2023-11-08 18:31:05.186215"
    )  # matches conftest's TODO.finished_at
    original_duration = 61.664511

    data = {
        project_name: {
            "tasks": {
                task_name: {
                    "created_at": "2023-11-08 18:30:03.517269",
                    "status": "finished",
                    "duration": original_duration,
                    "since": "",
                    "finished_at": f"{finished_at}",
                }
            }
        }
    }
    finish_day_start = finished_at.replace(hour=0, minute=0, second=0, microsecond=0)
    finish_day_end = finished_at + datetime.timedelta(hours=1)

    before = digest_handler.collect(data, finish_day_start, finish_day_end)
    assert before[project_name][task_name]["seconds"] == pytest.approx(
        original_duration
    )

    edited = task_handler.edit(data, project_name, task_name, duration_hours=2)

    # The finish day's total is preserved, not dropped to just the delta.
    after_finish_day = digest_handler.collect(edited, finish_day_start, finish_day_end)
    assert after_finish_day[project_name][task_name]["seconds"] == pytest.approx(
        original_duration
    )

    # The correction itself lands on today's digest, dated when it was made.
    today_start, today_end = digest_handler.day_window()
    after_today = digest_handler.collect(edited, today_start, today_end)
    assert after_today[project_name][task_name]["seconds"] == pytest.approx(
        2 * 3600 - original_duration
    )


def test_edit_on_running_task_does_not_disturb_its_open_session(
    test_data, patch_datetime_now
):
    """
    edit() appends an adjustment entry after the task's real open session
    (the one with `end: None` from the still-running task). A later
    finish() must still find and close that original open session rather
    than the adjustment entry that follows it.
    """
    project_name = "BEST"
    task_name = "UNTITLED_1"  # running per test_data
    task = test_data[project_name]["tasks"][task_name]
    task["sessions"] = [{"start": task["since"], "end": None}]

    edited = task_handler.edit(test_data, project_name, task_name, duration_hours=1)
    finished = task_handler.finish(edited, project_name, task_name)
    result = finished[project_name]["tasks"][task_name]

    assert result["status"] == settings.FINISHED
    assert result["sessions"][0]["end"] == f"{TEST_TIME_NOW}"  # original session closed
    assert result["sessions"][-1]["delta"] is not None  # adjustment entry untouched


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
