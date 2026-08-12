import os
import subprocess


def normalize(path):
    return os.path.realpath(path)


def resolve_project(links, cwd):
    """
    Longest-prefix match of `cwd` against linked directories. `links` is
    `{normalized_path: project_name}` — `hook link`/`hook unlink` already
    normalize keys before storing, so only `cwd` needs it here. This
    matters on the hot path an ambient shell hook runs on: it avoids one
    `os.path.realpath` (a stat syscall) per linked directory on every
    single `cd`/branch check, re-normalizing paths that were already
    normalized once, at link time. Linking a repo root also covers its
    subdirectories; an unrelated directory (anything not under a linked
    path) resolves to `None` rather than guessing a project from its name
    — the hook only ever touches directories the user explicitly linked.
    """
    cwd = normalize(cwd)
    best_path, best_project = None, None
    for linked_path, project_name in links.items():
        if cwd == linked_path or cwd.startswith(linked_path + os.sep):
            if best_path is None or len(linked_path) > len(best_path):
                best_path, best_project = linked_path, project_name
    return best_project


def current_branch(cwd, timeout=2):
    """
    Current git branch for `cwd`, or `None` if it's not a git repo, HEAD is
    detached, or git isn't available/times out. Errors are swallowed here
    rather than raised because this is on the hot path of an ambient shell
    hook: it must never be the reason a `cd` or prompt fails.

    Uses `symbolic-ref` rather than `rev-parse --abbrev-ref HEAD`: the
    latter fails on a brand-new repo with no commits yet (an "unborn"
    branch), which is exactly the state a just-linked project is likely
    to be in.
    """
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None
