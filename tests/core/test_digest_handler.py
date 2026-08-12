import datetime

from PyTM.core import digest_handler


def dt(*args):
    return datetime.datetime(*args)


def test_day_window_is_local_midnight_to_now():
    now = dt(2024, 1, 10, 15, 30)
    start, end = digest_handler.day_window(now)
    assert start == dt(2024, 1, 10, 0, 0)
    assert end == now


def test_week_window_defaults_to_saturday_start():
    # Wednesday 2024-01-10; most recent Saturday is 2024-01-06.
    now = dt(2024, 1, 10, 12, 0)
    start, end = digest_handler.week_window(now=now)
    assert start == dt(2024, 1, 6, 0, 0)
    assert end == now


def test_week_window_when_today_is_the_start_day():
    # Saturday itself: window starts at today's midnight, not 7 days back.
    now = dt(2024, 1, 6, 9, 0)
    start, end = digest_handler.week_window(now=now)
    assert start == dt(2024, 1, 6, 0, 0)


def test_week_window_respects_configured_start_day():
    now = dt(2024, 1, 10, 12, 0)  # Wednesday
    start, _ = digest_handler.week_window(week_start_day="monday", now=now)
    assert start == dt(2024, 1, 8, 0, 0)  # most recent Monday


def test_collect_sums_session_overlap_within_window():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "task-a": {
                    "duration": 7200,
                    "sessions": [
                        # entirely before today: excluded
                        {
                            "start": f"{dt(2024,1,9,10,0)}",
                            "end": f"{dt(2024,1,9,11,0)}",
                        },
                        # spans midnight into today: only the today portion counts
                        {
                            "start": f"{dt(2024,1,9,23,0)}",
                            "end": f"{dt(2024,1,10,1,0)}",
                        },
                        # entirely within today
                        {
                            "start": f"{dt(2024,1,10,9,0)}",
                            "end": f"{dt(2024,1,10,10,0)}",
                        },
                    ],
                }
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    seconds = breakdown["proj"]["task-a"]["seconds"]
    assert seconds == 3600 + 3600  # 1h of the overnight session + the 1h today session
    assert breakdown["proj"]["task-a"]["legacy"] is False


def test_collect_counts_open_session_up_to_now():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "running": {
                    "duration": 0,
                    "sessions": [{"start": f"{dt(2024,1,10,10,0)}", "end": None}],
                }
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    assert breakdown["proj"]["running"]["seconds"] == 7200  # 10:00 -> 12:00


def test_collect_counts_adjustment_delta_on_the_day_it_was_made():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "corrected": {
                    "duration": 9000,
                    "sessions": [
                        {
                            "start": f"{dt(2024,1,10,9,0)}",
                            "delta": 1800,
                            "end": f"{dt(2024,1,10,9,0)}",
                        }
                    ],
                }
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    assert breakdown["proj"]["corrected"]["seconds"] == 1800


def test_collect_falls_back_to_legacy_bucketing_when_no_sessions():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "old-task": {
                    "duration": 3600,
                    "status": "finished",
                    "finished_at": f"{dt(2024,1,10,8,0)}",
                }
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    assert breakdown["proj"]["old-task"]["seconds"] == 3600
    assert breakdown["proj"]["old-task"]["legacy"] is True


def test_collect_omits_legacy_task_finished_outside_window():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "old-task": {
                    "duration": 3600,
                    "status": "finished",
                    "finished_at": f"{dt(2024,1,9,8,0)}",
                }
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    assert "proj" not in breakdown


def test_collect_omits_legacy_task_with_no_finished_at_rather_than_guessing():
    now = dt(2024, 1, 10, 12, 0)
    window_start, window_end = digest_handler.day_window(now)
    data = {
        "proj": {
            "tasks": {
                "stuck-running": {"duration": 3600, "status": "running"},
            }
        }
    }
    breakdown = digest_handler.collect(data, window_start, window_end, now=now)
    assert breakdown == {}
