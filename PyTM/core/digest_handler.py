import datetime

from PyTM import settings


def _parse(ts):
    return datetime.datetime.fromisoformat(ts)


def _session_seconds_in_window(session, window_start, window_end, now):
    """
    Seconds of a single session that fall within [window_start, window_end).

    Adjustment entries written by `task_handler.edit` carry an explicit
    `delta` instead of a real interval — they represent a point-in-time
    correction, not time actually worked, so they're counted in full on
    the day the correction was made rather than time-weighted.
    """
    start = _parse(session["start"])
    if "delta" in session:
        return session["delta"] if window_start <= start < window_end else 0

    end = _parse(session["end"]) if session.get("end") else now
    overlap_start = max(start, window_start)
    overlap_end = min(end, window_end)
    if overlap_end <= overlap_start:
        return 0
    return (overlap_end - overlap_start).total_seconds()


def _legacy_seconds(task, window_start, window_end):
    """
    Tasks recorded before per-session tracking existed have no interval
    data to overlap against the window. Best-effort attribution: bucket
    the whole stored `duration` on the day the task was finished, since
    that's the only timestamp guaranteed to reflect when the work landed.
    A task with no `finished_at` (still running, or aborted, from before
    the upgrade) is left unattributed rather than guessed at — reporting
    nothing is safer than reporting it on the wrong day.
    """
    finished_at = task.get("finished_at")
    if not finished_at:
        return 0
    finished = _parse(finished_at)
    return task.get("duration", 0) if window_start <= finished < window_end else 0


def collect(data, window_start, window_end, now=None):
    """
    Returns `{project_name: {task_name: {"seconds": n, "legacy": bool}}}`
    for every task with nonzero time attributed to [window_start, window_end).
    `legacy=True` marks a best-effort (pre-session-tracking) attribution.
    """
    now = now or datetime.datetime.now()
    breakdown = {}
    for project_name, project in data.items():
        for task_name, task in project.get("tasks", {}).items():
            sessions = task.get("sessions")
            if sessions:
                seconds = sum(
                    _session_seconds_in_window(s, window_start, window_end, now)
                    for s in sessions
                )
                legacy = False
            else:
                seconds = _legacy_seconds(task, window_start, window_end)
                legacy = seconds > 0
            if seconds:
                breakdown.setdefault(project_name, {})[task_name] = {
                    "seconds": seconds,
                    "legacy": legacy,
                }
    return breakdown


def day_window(now=None):
    """Local-time midnight through now."""
    now = now or datetime.datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def week_window(week_start_day=None, now=None):
    """
    Local-time midnight of the most recent `week_start_day` (today counts)
    through now.
    """
    now = now or datetime.datetime.now()
    week_start_day = (week_start_day or settings.DEFAULT_WEEK_START).lower()
    target = settings.WEEKDAYS.index(week_start_day)
    days_since_start = (now.weekday() - target) % 7
    start = (now - datetime.timedelta(days=days_since_start)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, now
