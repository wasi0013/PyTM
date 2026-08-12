import json
import os
import tempfile

from filelock import FileLock

from PyTM import settings


def _default_path(path):
    """
    Resolves the effective path for a data-handler call. Falling back to
    `settings.data_filepath` here (instead of as a function default) means
    the current value of `settings.data_filepath` is used, not whatever it
    was when this module was first imported.
    """
    return path if path is not None else settings.data_filepath


def _directory_of(path):
    return os.path.dirname(os.path.abspath(str(path))) or "."


def _lock_path(path):
    return f"{path}.lock"


def _atomic_write(data, path):
    """
    Writes `data` to `path` without ever leaving a partial/corrupt file
    behind: the JSON is written to a temp file in the same directory,
    flushed and fsynced, then swapped into place with `os.replace`, which
    is atomic on both POSIX and Windows. If anything fails before the
    swap, the original file at `path` is left exactly as it was.
    """
    directory = _directory_of(path)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".pytm-tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def init_data(path=None, data=None):
    """
    Creates the data file at the given path.
    """
    path = _default_path(path)
    save_data({} if data is None else data, path)


def load_data(path=None):
    """
    Loads the data from the given path.
    """
    path = _default_path(path)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data, path=None):
    """
    Saves the data to the given path. Writes even when `data` is falsy
    (e.g. `{}`) so that legitimately emptying the store (removing the last
    project) is actually persisted; only an explicit `None` is treated as
    "nothing to save".
    """
    path = _default_path(path)
    if data is None:
        return
    os.makedirs(_directory_of(path), exist_ok=True)
    with FileLock(_lock_path(path)):
        _atomic_write(data, path)


def update(func, path=None):
    """
    Loads, mutates via `func`, and saves the data at `path` as a single
    locked operation. Holding the lock across both the load and the save
    means two concurrent `update()` calls on the same file can't
    interleave and silently lose one of the updates.
    """
    path = _default_path(path)
    os.makedirs(_directory_of(path), exist_ok=True)
    with FileLock(_lock_path(path)):
        data = load_data(path)
        _atomic_write(func(data), path)


def locked(path=None, timeout=-1):
    """
    Returns the same file lock `save_data`/`update` use for `path`, for a
    caller that needs several reads/writes on `path` to happen as one
    atomic unit — more than a single `update()` call covers. `timeout` is
    in seconds; -1 (the default) blocks indefinitely, matching
    `save_data`/`update`.

    Callers must write with `write_unlocked` inside the `with` block, not
    `save_data`/`update` — those acquire this same lock themselves, and a
    second acquisition from within the first, via a different `FileLock`
    instance on the same path, would deadlock rather than reentering.
    """
    path = _default_path(path)
    os.makedirs(_directory_of(path), exist_ok=True)
    return FileLock(_lock_path(path), timeout=timeout)


def write_unlocked(data, path=None):
    """
    Writes `data` to `path` atomically without acquiring the lock. For
    use only inside a `with locked(path):` block; everywhere else, use
    `save_data`.
    """
    path = _default_path(path)
    if data is None:
        return
    os.makedirs(_directory_of(path), exist_ok=True)
    _atomic_write(data, path)
