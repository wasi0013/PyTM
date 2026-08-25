import os
import subprocess
import threading

import pytest
from filelock import Timeout

from PyTM import settings
from PyTM.core import backup_handler, data_handler


def make_bare_remote(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    return str(remote)


def test_is_repo_false_for_plain_directory(tmp_path):
    assert backup_handler.is_repo(str(tmp_path)) is False


def test_init_repo_creates_git_repo_and_gitignore(tmp_path):
    repo_root = str(tmp_path / "repo")
    assert backup_handler.init_repo(repo_root) is True
    assert backup_handler.is_repo(repo_root) is True
    assert (tmp_path / "repo" / ".gitignore").exists()
    info = backup_handler.last_commit_info(repo_root)
    assert info is not None
    assert "initial commit" in info["message"]


def test_init_repo_returns_false_when_initial_commit_fails(tmp_path, monkeypatch):
    """
    `init_repo`'s return value is what `backup enable` reports success or
    failure from — it must not claim success when the initial commit
    (the whole point of enabling) didn't actually happen.
    """
    monkeypatch.setattr(backup_handler, "commit_all", lambda *a, **k: False)
    assert backup_handler.init_repo(str(tmp_path / "repo")) is False


def test_init_repo_is_idempotent(tmp_path):
    repo_root = str(tmp_path / "repo")
    assert backup_handler.init_repo(repo_root) is True
    (tmp_path / "repo" / "data.json").write_text("{}")
    assert backup_handler.init_repo(repo_root) is True
    assert backup_handler.has_uncommitted_changes(repo_root) is False


def test_commit_all_stages_and_commits_new_file(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    (tmp_path / "repo" / "data.json").write_text('{"a": 1}')
    assert backup_handler.has_uncommitted_changes(repo_root) is True
    assert backup_handler.commit_all(repo_root, "wrote data.json") is True
    assert backup_handler.has_uncommitted_changes(repo_root) is False
    info = backup_handler.last_commit_info(repo_root)
    assert info["message"] == "wrote data.json"


def test_commit_all_is_a_noop_when_clean(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    before = backup_handler.last_commit_info(repo_root)
    assert backup_handler.commit_all(repo_root, "nothing changed") is True
    after = backup_handler.last_commit_info(repo_root)
    assert before == after  # no empty commit was created


def test_commit_all_on_non_repo_returns_false(tmp_path):
    assert backup_handler.commit_all(str(tmp_path), "msg") is False


def test_gitignore_excludes_lock_files(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    (tmp_path / "repo" / "data.json.lock").write_text("")
    assert backup_handler.has_uncommitted_changes(repo_root) is False


def test_set_get_and_remove_remote(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    remote_url = make_bare_remote(tmp_path)
    assert backup_handler.get_remote_url(repo_root) is None
    assert backup_handler.set_remote(repo_root, remote_url) is True
    assert backup_handler.get_remote_url(repo_root) == remote_url
    # setting again (a different URL) updates rather than erroring
    other_url = make_bare_remote(tmp_path)
    assert backup_handler.set_remote(repo_root, other_url) is True
    assert backup_handler.get_remote_url(repo_root) == other_url
    assert backup_handler.remove_remote(repo_root) is True
    assert backup_handler.get_remote_url(repo_root) is None


def test_push_without_remote_configured_fails_cleanly(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    ok, message = backup_handler.push(repo_root)
    assert ok is False
    assert "remote" in message.lower()


def test_push_to_bare_remote_round_trips(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    remote_url = make_bare_remote(tmp_path)
    backup_handler.set_remote(repo_root, remote_url)
    (tmp_path / "repo" / "data.json").write_text('{"a": 1}')
    backup_handler.commit_all(repo_root, "data")
    ok, message = backup_handler.push(repo_root)
    assert ok is True, message

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", remote_url, str(clone)], check=True)
    assert (clone / "data.json").read_text() == '{"a": 1}'


def test_auto_commit_ignores_writes_outside_data_folder(tmp_path, monkeypatch):
    """
    Safety property: a write to an arbitrary path (as core tests and any
    future `path=` override use) must never reach git, even if backup
    happens to be enabled, unless that path is actually inside
    `settings.data_folder`.
    """
    data_folder = tmp_path / "pytm-home"
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    backup_handler.init_repo(str(data_folder))
    data_handler.save_data(
        {"config": {"backup": {"enabled": True}}}, str(data_folder / "state.json")
    )

    calls = []
    monkeypatch.setattr(
        backup_handler,
        "_run_git",
        lambda *a, **k: calls.append(a) or None,
    )

    outside = tmp_path / "elsewhere.json"
    outside.write_text("{}")
    backup_handler.auto_commit(str(outside))
    assert calls == []


def test_auto_commit_noop_when_disabled(tmp_path, monkeypatch):
    data_folder = tmp_path / "pytm-home"
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    backup_handler.init_repo(str(data_folder))
    target = data_folder / "data.json"
    target.write_text('{"a": 1}')
    backup_handler.auto_commit(str(target))
    assert backup_handler.has_uncommitted_changes(str(data_folder)) is True


def test_auto_commit_commits_when_enabled(tmp_path, monkeypatch):
    data_folder = tmp_path / "pytm-home"
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    backup_handler.init_repo(str(data_folder))
    data_handler.save_data(
        {"config": {"backup": {"enabled": True}}}, str(data_folder / "state.json")
    )
    target = data_folder / "data.json"
    target.write_text('{"a": 1}')
    backup_handler.auto_commit(str(target))
    assert backup_handler.has_uncommitted_changes(str(data_folder)) is False


def test_run_git_returns_none_when_git_is_missing(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("git not found")

    monkeypatch.setattr(subprocess, "run", boom)
    assert backup_handler._run_git(["status"], str(tmp_path)) is None


def test_init_repo_returns_false_when_git_init_fails(tmp_path, monkeypatch):
    real_run_git = backup_handler._run_git

    def fake(args, cwd, timeout=5, with_identity=False):
        if args[:1] == ["init"]:
            return subprocess.CompletedProcess(args, 1, "", "boom")
        return real_run_git(args, cwd, timeout=timeout, with_identity=with_identity)

    monkeypatch.setattr(backup_handler, "_run_git", fake)
    assert backup_handler.init_repo(str(tmp_path / "repo")) is False


def test_has_uncommitted_changes_returns_none_on_git_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_handler, "_run_git", lambda *a, **k: None)
    assert backup_handler.has_uncommitted_changes(str(tmp_path)) is None


def test_commit_all_returns_false_when_add_fails(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    real_run_git = backup_handler._run_git

    def fake(args, cwd, timeout=5, with_identity=False):
        if args[:1] == ["add"]:
            return None
        return real_run_git(args, cwd, timeout=timeout, with_identity=with_identity)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(backup_handler, "_run_git", fake)
        assert backup_handler.commit_all(repo_root, "msg") is False


def test_commit_all_returns_false_when_status_fails(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    (tmp_path / "repo" / "new.txt").write_text("x")
    real_run_git = backup_handler._run_git

    def fake(args, cwd, timeout=5, with_identity=False):
        if args[:1] == ["status"]:
            return None
        return real_run_git(args, cwd, timeout=timeout, with_identity=with_identity)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(backup_handler, "_run_git", fake)
        assert backup_handler.commit_all(repo_root, "msg") is False


def test_commit_all_returns_false_on_lock_timeout(tmp_path, monkeypatch):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)

    def raise_timeout(*args, **kwargs):
        raise Timeout(backup_handler._backup_lock_path(repo_root))

    monkeypatch.setattr(backup_handler, "_backup_lock", raise_timeout)
    assert backup_handler.commit_all(repo_root, "msg") is False


def test_push_without_a_determinable_branch_fails_cleanly(tmp_path, monkeypatch):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    backup_handler.set_remote(repo_root, make_bare_remote(tmp_path))
    monkeypatch.setattr(backup_handler.hook_handler, "current_branch", lambda cwd: None)
    ok, message = backup_handler.push(repo_root)
    assert ok is False
    assert "branch" in message.lower()


def test_push_returns_false_when_git_push_cannot_run(tmp_path, monkeypatch):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    backup_handler.set_remote(repo_root, make_bare_remote(tmp_path))
    real_run_git = backup_handler._run_git

    def fake(args, cwd, timeout=5, with_identity=False):
        if args[:1] == ["push"]:
            return None
        return real_run_git(args, cwd, timeout=timeout, with_identity=with_identity)

    monkeypatch.setattr(backup_handler, "_run_git", fake)
    ok, message = backup_handler.push(repo_root)
    assert ok is False
    assert "timed out" in message.lower() or "failed" in message.lower()


def test_push_returns_false_on_git_push_error(tmp_path):
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)
    # Points at a path that isn't a git repo at all, so `git push` fails.
    backup_handler.set_remote(repo_root, str(tmp_path / "not-a-repo"))
    ok, message = backup_handler.push(repo_root, branch="master")
    assert ok is False
    assert message


def test_last_commit_info_returns_none_before_any_commit(tmp_path):
    repo_root = str(tmp_path / "repo")
    os.makedirs(repo_root)
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    assert backup_handler.last_commit_info(repo_root) is None


def test_auto_commit_skips_when_enabled_but_repo_missing(tmp_path, monkeypatch):
    data_folder = tmp_path / "pytm-home"
    data_folder.mkdir()
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    data_handler.save_data(
        {"config": {"backup": {"enabled": True}}}, str(data_folder / "state.json")
    )
    target = data_folder / "data.json"
    target.write_text("{}")
    backup_handler.auto_commit(str(target))  # must not raise, no repo to commit to
    assert backup_handler.is_repo(str(data_folder)) is False


def test_auto_commit_never_raises_on_git_failure(tmp_path, monkeypatch):
    data_folder = tmp_path / "pytm-home"
    monkeypatch.setattr(settings, "data_folder", str(data_folder))
    monkeypatch.setattr(settings, "state_filepath", str(data_folder / "state.json"))
    backup_handler.init_repo(str(data_folder))
    data_handler.save_data(
        {"config": {"backup": {"enabled": True}}}, str(data_folder / "state.json")
    )

    def boom(*args, **kwargs):
        raise OSError("simulated git failure")

    monkeypatch.setattr(backup_handler, "_run_git", boom)
    target = data_folder / "data.json"
    target.write_text('{"a": 1}')
    backup_handler.auto_commit(str(target))  # must not raise


def test_commit_all_concurrent_calls_never_lose_a_commit(tmp_path):
    """
    Concurrency test for the git-index race `_backup_lock` exists to
    close: without it, two `git add`/`git commit` pairs running at once
    can collide on git's own `.git/index.lock` and one commit silently
    vanishes. Every writer here changes a distinct file, so a clean
    working tree at the end proves every one of them actually landed.
    """
    repo_root = str(tmp_path / "repo")
    backup_handler.init_repo(repo_root)

    def write_and_commit(i):
        (tmp_path / "repo" / f"file-{i}.txt").write_text(str(i))
        backup_handler.commit_all(repo_root, f"write file-{i}")

    threads = [threading.Thread(target=write_and_commit, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert backup_handler.has_uncommitted_changes(repo_root) is False
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, capture_output=True, text=True
    ).stdout.split()
    assert sorted(tracked) == sorted(
        [".gitignore"] + [f"file-{i}.txt" for i in range(10)]
    )
