import json
import os
import threading

import pytest

from PyTM import settings
from PyTM.core import data_handler


def test_init_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data_handler.init_data(tmp_path)
    assert tmp_path.read() == "{}"


def test_load_data_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    tmp_path.write(json.dumps(data))
    assert data_handler.load_data(tmp_path) == data


def test_load_data_doesnot_exists(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    assert data_handler.load_data(tmp_path) == {}


def test_save_data(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    data = {"user": "test"}
    data_handler.save_data(data, tmp_path)
    assert tmp_path.read() == json.dumps(data)


def test_update(tmpdir):
    f = lambda d: {"user": "test"}
    tmp_path = tmpdir.join("pytm-test.json")
    tmp_path.write("[]")
    data_handler.update(f, tmp_path)
    assert tmp_path.read() == '{"user": "test"}'


def test_save_data_persists_empty_dict(tmpdir):
    """
    Regression test: `save_data` used to silently no-op on falsy data, so
    e.g. removing the last project would leave the old file untouched and
    the project would reappear on next load. An explicit empty store must
    actually be written.
    """
    tmp_path = tmpdir.join("pytm-test.json")
    data_handler.save_data({"a": 1}, tmp_path)
    data_handler.save_data({}, tmp_path)
    assert tmp_path.read() == "{}"
    assert data_handler.load_data(tmp_path) == {}


def test_save_data_none_is_a_noop(tmpdir):
    tmp_path = tmpdir.join("pytm-test.json")
    tmp_path.write(json.dumps({"a": 1}))
    data_handler.save_data(None, tmp_path)
    assert tmp_path.read() == json.dumps({"a": 1})


def test_default_path_resolved_at_call_time(tmp_path, monkeypatch):
    """
    Regression test: the data/state file paths used to be bound as
    function-default arguments, which freezes them to whatever
    `settings.data_filepath` was when `data_handler` was first imported.
    Monkeypatching `settings.data_filepath` afterwards (as tests and any
    future config-reload need to) must actually take effect.
    """
    redirected = tmp_path / "redirected.json"
    monkeypatch.setattr(settings, "data_filepath", str(redirected))
    data_handler.save_data({"redirected": True}, path=None)
    assert redirected.exists()
    assert data_handler.load_data(path=None) == {"redirected": True}


def test_save_data_survives_a_crash_mid_write(tmp_path, monkeypatch):
    """
    Crash-injection test: if the write fails partway through (process
    killed, disk error, etc.) the original file must be left exactly as it
    was, and no leftover temp file should remain.
    """
    target = tmp_path / "data.json"
    target.write_text('{"existing": true}')

    def boom(*args, **kwargs):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(data_handler.os, "fsync", boom)

    with pytest.raises(OSError):
        data_handler.save_data({"new": "data"}, str(target))

    assert target.read_text() == '{"existing": true}'
    leftovers = [p for p in os.listdir(tmp_path) if p.startswith(".pytm-tmp-")]
    assert leftovers == []


def test_update_concurrent_does_not_lose_updates(tmp_path):
    """
    Concurrency test scoped to what the lock actually protects: `update()`
    holds the lock across its whole load-mutate-save cycle, so concurrent
    callers targeting the same file must not clobber each other.
    """
    target = tmp_path / "data.json"
    data_handler.save_data({"count": 0}, str(target))

    def increment():
        data_handler.update(
            lambda d: {**d, "count": d.get("count", 0) + 1}, str(target)
        )

    threads = [threading.Thread(target=increment) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert data_handler.load_data(str(target))["count"] == 20


def test_locked_serializes_concurrent_readmodifywrite_sequences(tmp_path):
    """
    Regression: `hook resolve --apply` reads state, then makes up to two
    separate load/mutate/save round trips — more than a single `update()`
    call covers — on a path invoked automatically and frequently (every
    shell prompt change, potentially from several terminals at once). A
    plain load/mutate/save per step lets one caller's write be silently
    clobbered by another's stale in-memory copy. `locked()` +
    `write_unlocked()` exist so a caller can hold the lock across its
    whole multi-step sequence instead.
    """
    target = tmp_path / "state.json"
    data_handler.save_data({"count": 0}, str(target))

    def increment_twice():
        with data_handler.locked(str(target)):
            data = data_handler.load_data(str(target))
            data["count"] = data.get("count", 0) + 1
            data_handler.write_unlocked(data, str(target))
            data = data_handler.load_data(str(target))
            data["count"] = data.get("count", 0) + 1
            data_handler.write_unlocked(data, str(target))

    threads = [threading.Thread(target=increment_twice) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert data_handler.load_data(str(target))["count"] == 20


def test_write_unlocked_none_is_a_noop(tmp_path):
    target = tmp_path / "state.json"
    data_handler.save_data({"a": 1}, str(target))
    data_handler.write_unlocked(None, str(target))
    assert data_handler.load_data(str(target)) == {"a": 1}


def test_save_data_survives_a_broken_backup_hook(tmp_path, monkeypatch):
    """
    A failure in the git auto-backup hook (a bug in `backup_handler`
    included) must never surface as a write failure — the hook is
    best-effort by design, layered behind its own writes.
    """
    from PyTM.core import backup_handler

    def boom(*args, **kwargs):
        raise RuntimeError("simulated backup_handler bug")

    monkeypatch.setattr(backup_handler, "auto_commit", boom)
    target = tmp_path / "data.json"
    data_handler.save_data({"a": 1}, str(target))
    assert data_handler.load_data(str(target)) == {"a": 1}
