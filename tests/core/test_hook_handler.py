from PyTM.core import hook_handler


def linked(pairs):
    """
    Builds a `links` dict the way `hook link` actually stores one: keys
    pre-normalized via `hook_handler.normalize`. `resolve_project` relies
    on that invariant (it only normalizes `cwd`, not the stored keys, to
    avoid redundant syscalls on its hot path), so tests must match it
    rather than hand a raw literal path and rely on the function to fix
    it up.
    """
    return {hook_handler.normalize(path): project for path, project in pairs.items()}


def test_resolve_project_exact_match():
    links = linked({"/home/dev/proj-a": "proj-a"})
    assert hook_handler.resolve_project(links, "/home/dev/proj-a") == "proj-a"


def test_resolve_project_matches_subdirectory():
    links = linked({"/home/dev/proj-a": "proj-a"})
    assert hook_handler.resolve_project(links, "/home/dev/proj-a/src/pkg") == "proj-a"


def test_resolve_project_does_not_match_unrelated_directory():
    links = linked({"/home/dev/proj-a": "proj-a"})
    assert hook_handler.resolve_project(links, "/home/dev/other") is None
    assert hook_handler.resolve_project(links, "/home/dev/proj-a-other") is None


def test_resolve_project_picks_longest_matching_prefix():
    links = linked(
        {
            "/home/dev": "workspace",
            "/home/dev/proj-a": "proj-a",
        }
    )
    assert hook_handler.resolve_project(links, "/home/dev/proj-a/src") == "proj-a"
    assert hook_handler.resolve_project(links, "/home/dev/other") == "workspace"


def test_resolve_project_with_no_links_returns_none():
    assert hook_handler.resolve_project({}, "/anywhere") is None


def test_resolve_project_does_not_match_an_unnormalized_stored_key(tmp_path):
    """
    Documents the invariant `resolve_project` now relies on for its
    hot-path optimization: it only normalizes `cwd`, not the stored
    keys, so a `links` dict with an unnormalized key (never produced by
    `hook link` itself, but possible via a hand-edited state.json) simply
    won't match rather than being silently fixed up. `..` forces
    `realpath` to actually simplify the path, regardless of platform.
    """
    real = tmp_path / "proj-a"
    real.mkdir()
    unnormalized_key = str(tmp_path / "sub" / ".." / "proj-a")
    links = {unnormalized_key: "proj-a"}
    assert hook_handler.resolve_project(links, str(real)) is None


def test_current_branch_outside_git_repo_returns_none(tmp_path):
    assert hook_handler.current_branch(str(tmp_path)) is None


def test_current_branch_inside_git_repo(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    assert hook_handler.current_branch(str(tmp_path)) == "main"
