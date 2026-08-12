import datetime

from PyTM import settings


def calculate_duration(date1, date2):
    return abs(
        (
            datetime.datetime.fromisoformat(date1)
            - datetime.datetime.fromisoformat(date2)
        ).total_seconds()
    )


def _close_open_session(task, end):
    """
    Closes the most recent open session (`end is None`), if any. Tasks
    created before the `sessions` field existed won't have one to close —
    that's fine, it's the caller's job to still account for `duration`.
    """
    sessions = task.get("sessions") or []
    for session in reversed(sessions):
        if session.get("end") is None:
            session["end"] = end
            return


def create(data, project_name, task_name):
    """Create and/or start/resume the task.

    Idempotent: calling this on a task that's already running is a no-op
    rather than resetting `since` to now, which would silently drop the
    time already accrued since it started. This matters once ambient
    hooks can call `start`/`switch` repeatedly on a task that's already
    active.
    """
    if data.get(project_name):
        tasks = data.get(project_name)["tasks"]
        now = f"{datetime.datetime.now()}"
        existing = tasks.get(task_name)
        if existing:
            if existing.get("status") == settings.STARTED:
                return data
            existing["status"] = settings.STARTED
            existing["since"] = now
            existing.setdefault("sessions", []).append({"start": now, "end": None})
        else:
            tasks[task_name] = {
                "created_at": now,
                "status": settings.STARTED,
                "duration": 0,
                "since": now,
                "sessions": [{"start": now, "end": None}],
            }
    return data


def pause(data, project_name, task_name):
    """Pause the task.

    No-op unless the task is currently running: pausing an already
    paused/finished/aborted task must not raise (ambient hooks may call
    this redundantly) and must not overwrite a terminal status.
    """
    if data.get(project_name):
        task = data.get(project_name)["tasks"].get(task_name)
        if task and task.get("status") == settings.STARTED:
            now = f"{datetime.datetime.now()}"
            since = task.get("since")
            if since:
                task["duration"] += calculate_duration(now, since)
                _close_open_session(task, now)
            task["status"] = settings.PAUSED
            task["since"] = ""
    return data


def finish(data, project_name, task_name):
    """Finish the task.

    No-op unless the task is running or paused: finishing an
    already-finished/aborted task must not raise and must not clobber the
    original `finished_at`.
    """
    if data.get(project_name):
        task = data.get(project_name)["tasks"].get(task_name)
        if task and task.get("status") in (settings.STARTED, settings.PAUSED):
            now = f"{datetime.datetime.now()}"
            since = task.get("since")
            if since:
                task["duration"] += calculate_duration(now, since)
                _close_open_session(task, now)
                task["since"] = ""
            task["status"] = settings.FINISHED
            task["finished_at"] = now
    return data


def status(data, project_name, task_name):
    """Status of the task"""
    if data.get(project_name):
        if data.get(project_name)["tasks"].get(task_name):
            return data.get(project_name)["tasks"][task_name]["status"]


def abort(data, project_name, task_name):
    """Abort the task.

    No-op unless the task is running or paused. Unlike the old
    implementation, this now accumulates any time logged since the last
    resume into `duration` and closes the open session instead of
    silently discarding it and leaving a dangling open session behind.
    """
    if data.get(project_name):
        task = data.get(project_name)["tasks"].get(task_name)
        if task and task.get("status") in (settings.STARTED, settings.PAUSED):
            since = task.get("since")
            if since:
                now = f"{datetime.datetime.now()}"
                task["duration"] += calculate_duration(now, since)
                _close_open_session(task, now)
                task["since"] = ""
            task["status"] = settings.ABORTED
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


def pause_all(data, project_name):
    """
    Pauses every currently running task within a project.

    Used when switching away from a project entirely (e.g. an ambient
    hook `cd`-ing to a different linked directory): `state`'s
    `CURRENT_TASK` only tracks one task, but a project can have another
    task left running from an earlier visit (started manually, or by a
    hook resolve that didn't get to update state before the directory
    changed again). Pausing only the recorded current task would leave
    that other one silently accruing time in the background.
    """
    if data.get(project_name):
        for task_name, task in data[project_name]["tasks"].items():
            if task.get("status") == settings.STARTED:
                pause(data, project_name, task_name)
    return data


def switch(data, project_name, to_task_name):
    """
    Atomically pauses every running task in `project_name` and
    starts/resumes `to_task_name`, all within a single locked
    read-modify-write. This closes the gap where switching tasks used to
    be two separate, independently-locked `update()` calls: a crash
    between them could leave the old task paused with nothing active, or
    (worse) two tasks simultaneously marked running.

    Deliberately pauses *every* running task via `pause_all` rather than
    a single caller-supplied "from" task: a project can have a task left
    running that `state`'s recorded current task doesn't know about
    (started manually, or by an earlier hook resolve that didn't get to
    update state), and pausing only the recorded one would leave that
    other task silently double-accruing time alongside the new one.
    """
    data = pause_all(data, project_name)
    data = create(data, project_name, to_task_name)
    return data


def edit(data, project_name, task_name, duration_hours):
    """
    Manually corrects a task's total recorded duration to `duration_hours`
    (hours, float). Rather than overwriting `duration` in a way that
    would silently drift out of sync with the `sessions` log the
    today/week digests rely on, the difference is recorded as a
    zero-length "adjustment" session dated now, so a correction shows up
    on the digest for the day it was made.

    A task with no `sessions` yet (pre-migration, digested today via
    `digest_handler`'s finished_at-bucketed legacy fallback) gets that
    original attribution seeded as a session first, dated on its
    `finished_at`. Without this, adding only the delta would flip the
    task from the legacy fallback (which attributes its *full* duration)
    to the session-based path (which would then only see the delta),
    silently dropping its original duration from every digest it used to
    show up in.
    """
    if data.get(project_name):
        task = data.get(project_name)["tasks"].get(task_name)
        if task:
            new_duration = duration_hours * 3600
            original_duration = task.get("duration", 0)
            sessions = task.setdefault("sessions", [])
            if not sessions and task.get("finished_at"):
                finished_at = task["finished_at"]
                sessions.append(
                    {
                        "start": finished_at,
                        "end": finished_at,
                        "delta": original_duration,
                    }
                )
            delta = new_duration - original_duration
            now = f"{datetime.datetime.now()}"
            sessions.append({"start": now, "end": now, "delta": delta})
            task["duration"] = new_duration
    return data
