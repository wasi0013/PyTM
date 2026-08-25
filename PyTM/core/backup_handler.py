import os
import shutil
import subprocess

from filelock import FileLock, Timeout

from PyTM import settings
from PyTM.core import data_handler, hook_handler

# Commits made by PyTM itself always use this identity, regardless of
# whatever (if anything) `git config user.name`/`user.email` resolve to on
# the machine — a write must not silently go unbacked-up just because the
# user never configured a global git identity.
GIT_IDENTITY = ["-c", "user.name=PyTM", "-c", "user.email=pytm-backup@localhost"]

GITIGNORE_CONTENT = "*.lock\n.pytm-tmp-*\n.backup.lock\n"

LOCK_TIMEOUT = 2


def _backup_lock_path(repo_root):
    return os.path.join(repo_root, ".backup.lock")


def _backup_lock(repo_root, timeout=LOCK_TIMEOUT):
    """
    Git operations get their own lock, separate from `data_handler`'s
    per-JSON-file `FileLock`s. `git add`/`git commit` race on git's own
    `.git/index.lock` if two `pytm` processes run them at the same time
    (e.g. two terminals writing state via ambient hooks); without this,
    the loser's commit would just silently vanish instead of erroring.
    """
    return FileLock(_backup_lock_path(repo_root), timeout=timeout)


def _run_git(args, cwd, timeout=5, with_identity=False):
    cmd = ["git"]
    if with_identity:
        cmd += GIT_IDENTITY
    cmd += args
    try:
        return subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.SubprocessError):
        return None


def is_git_available():
    return shutil.which("git") is not None


def is_repo(repo_root):
    """
    True only when `repo_root` is itself a git worktree root. Deliberately
    an `os.path.isdir` check, not `git rev-parse --git-dir`: `rev-parse`
    walks *up* the directory tree looking for a repo, so if some ancestor
    of `repo_root` (the user's home directory, say, tracked by a dotfiles
    repo) happens to be a git repo, `rev-parse` would report one here too
    — and every backup commit would land in *that* unrelated repo instead
    of a dedicated one at `repo_root`.
    """
    return os.path.isdir(os.path.join(repo_root, ".git"))


def init_repo(repo_root):
    """
    Initializes `repo_root` as its own git repo (idempotent — safe to call
    on one that already exists) and makes an initial commit covering
    whatever's already there, so `backup enable` on an existing `~/.pytm`
    captures current data immediately instead of waiting for the next
    write.
    """
    os.makedirs(repo_root, exist_ok=True)
    if not is_repo(repo_root):
        result = _run_git(["init"], repo_root)
        if result is None or result.returncode != 0:
            return False
    gitignore_path = os.path.join(repo_root, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(GITIGNORE_CONTENT)
    # Propagate this rather than unconditionally returning True: `backup
    # enable` reports success straight from this return value, and
    # claiming success with zero commits made (lock contention, a git
    # failure past `init`) is the wrong failure mode for a feature whose
    # whole pitch is the data guarantee.
    return commit_all(repo_root, "PyTM backup: initial commit")


def has_uncommitted_changes(repo_root):
    """
    Returns True/False, or None if git status couldn't be read at all.
    """
    result = _run_git(["status", "--porcelain"], repo_root)
    if result is None or result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def commit_all(repo_root, message, timeout=LOCK_TIMEOUT):
    """
    Stages everything under `repo_root` and commits, serialized under
    `_backup_lock` so concurrent callers can't race on git's own index
    lock. A lock-acquire timeout is treated as a safe skip, not a
    failure: `git add -A` always stages the *whole* working tree, so
    whatever this call missed is picked up whole by the next commit
    (auto or manual `pytm backup commit`) — at most the most recent write
    is ever left briefly uncommitted, never lost.

    Returns True if the repo ends up clean (something was committed, or
    there was nothing to commit); False on a real git failure or lock
    contention.
    """
    if not is_repo(repo_root):
        return False
    try:
        with _backup_lock(repo_root, timeout=timeout):
            add_result = _run_git(["add", "-A"], repo_root)
            if add_result is None or add_result.returncode != 0:
                return False
            status = _run_git(["status", "--porcelain"], repo_root)
            if status is None or status.returncode != 0:
                return False
            if not status.stdout.strip():
                return True
            commit_result = _run_git(
                ["commit", "-m", message], repo_root, with_identity=True
            )
            return commit_result is not None and commit_result.returncode == 0
    except Timeout:
        return False


def get_remote_url(repo_root, name=None):
    name = name or settings.DEFAULT_BACKUP_REMOTE
    result = _run_git(["remote", "get-url", name], repo_root)
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip() or None


def set_remote(repo_root, url, name=None):
    name = name or settings.DEFAULT_BACKUP_REMOTE
    if get_remote_url(repo_root, name) is not None:
        result = _run_git(["remote", "set-url", name, url], repo_root)
    else:
        result = _run_git(["remote", "add", name, url], repo_root)
    return result is not None and result.returncode == 0


def remove_remote(repo_root, name=None):
    name = name or settings.DEFAULT_BACKUP_REMOTE
    result = _run_git(["remote", "remove", name], repo_root)
    return result is not None and result.returncode == 0


def push(repo_root, name=None, branch=None, timeout=15):
    """
    Manual only — auto-backup never calls this. Auto-commit runs from
    inside `data_handler`'s write path, potentially while a `FileLock` on
    `state.json` is held (`hook resolve --apply`); a network push from
    there could block that lock for the full push timeout and stall
    every other terminal's ambient hook. Pushing stays an explicit,
    user-triggered action.
    """
    name = name or settings.DEFAULT_BACKUP_REMOTE
    if get_remote_url(repo_root, name) is None:
        return False, f"No remote named '{name}' configured."
    branch = branch or hook_handler.current_branch(repo_root)
    if not branch:
        return False, "Could not determine the current branch to push."
    result = _run_git(["push", name, branch], repo_root, timeout=timeout)
    if result is None:
        return False, "git push failed to run or timed out."
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "git push failed").strip()
    return True, f"Pushed {branch} to {name}."


def last_commit_info(repo_root):
    result = _run_git(["log", "-1", "--format=%H%x1f%cI%x1f%s"], repo_root)
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return None
    sha, date, message = result.stdout.strip().split("\x1f", 2)
    return {"hash": sha, "date": date, "message": message}


def _is_enabled(state):
    return bool(state.get("config", {}).get("backup", {}).get("enabled"))


def auto_commit(path):
    """
    Fired after every successful atomic write in `data_handler`. Silent
    and best-effort by design: a backup hiccup (disabled, git missing,
    lock contention, anything) must never be the reason a `pytm` write
    fails or an ambient shell hook breaks.

    Only fires for writes inside `settings.data_folder` (the backup
    repo's root). This matters beyond correctness: `data_handler`'s
    public functions accept an arbitrary `path=` override, and tests use
    that to write to throwaway tmp files with `settings.data_folder`
    left pointed at whatever it actually is on the machine running the
    tests. Without this check, running the test suite on a machine that
    has backup enabled on its real `~/.pytm` could reach out and run git
    commands against it.
    """
    try:
        repo_root = os.path.abspath(settings.data_folder)
        target = os.path.abspath(str(path))
        if os.path.commonpath([repo_root, target]) != repo_root:
            return
        state = data_handler.load_data(settings.state_filepath)
        if not _is_enabled(state):
            return
        if not is_repo(repo_root):
            return
        commit_all(repo_root, f"auto: {os.path.basename(target)} updated")
    except Exception:
        pass
