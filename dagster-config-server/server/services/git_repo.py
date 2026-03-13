from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import cast

import pygit2

from .config import (
    get_git_author_email,
    get_git_author_name,
    get_git_branch,
    get_git_repo_url,
    get_git_token,
    get_git_username,
    get_repo_workdir,
)

_repo_lock = Lock()


def _get_hard_reset_mode() -> int:
    reset_mode = getattr(pygit2, "ResetMode", None)
    if reset_mode is not None and hasattr(reset_mode, "HARD"):
        return reset_mode.HARD

    enums = getattr(pygit2, "enums", None)
    if enums is not None and hasattr(enums, "ResetMode") and hasattr(enums.ResetMode, "HARD"):
        return enums.ResetMode.HARD

    legacy_mode = getattr(pygit2, "GIT_RESET_HARD", None)
    if legacy_mode is None:
        raise RuntimeError("No compatible hard reset mode found in pygit2.")
    return legacy_mode


def _build_callbacks() -> pygit2.RemoteCallbacks | None:
    repo_url = get_git_repo_url()
    token = get_git_token()
    username = get_git_username()

    if token:
        return pygit2.RemoteCallbacks(credentials=pygit2.UserPass(username, token))

    if repo_url.startswith("git@") or repo_url.startswith("ssh://"):
        return pygit2.RemoteCallbacks(credentials=pygit2.KeypairFromAgent(username))

    return None


def _clone_or_open_repo() -> pygit2.Repository:
    repo_dir = Path(get_repo_workdir())
    repo_url = get_git_repo_url()
    branch = get_git_branch()
    callbacks = _build_callbacks()

    if (repo_dir / ".git").exists():
        return pygit2.Repository(str(repo_dir))

    repo_dir.mkdir(parents=True, exist_ok=True)
    return pygit2.clone_repository(
        repo_url,
        str(repo_dir),
        checkout_branch=branch,
        callbacks=callbacks,
    )


def _sync_branch(repo: pygit2.Repository) -> None:
    branch = get_git_branch()
    callbacks = _build_callbacks()
    remote = repo.remotes["origin"]
    remote.fetch(callbacks=callbacks)

    remote_ref_name = f"refs/remotes/origin/{branch}"
    try:
        remote_ref = repo.references[remote_ref_name]
    except KeyError:
        raise LookupError(f"Remote branch not found: origin/{branch}")


    local_ref_name = f"refs/heads/{branch}"
    if local_ref_name not in repo.references:
        remote_commit = repo[remote_ref.target]
        if not isinstance(remote_commit, pygit2.Commit):
            raise TypeError("Remote branch head is not a commit.")
        repo.create_branch(branch, remote_commit, force=True)

    repo.references[local_ref_name].set_target(remote_ref.target)
    repo.set_head(local_ref_name)
    repo.checkout_head(
        strategy=pygit2.GIT_CHECKOUT_FORCE | pygit2.GIT_CHECKOUT_RECREATE_MISSING
    )
    repo.reset(remote_ref.target, _get_hard_reset_mode())


def ensure_repo_ready(sync_with_remote: bool = True) -> str:
    with _repo_lock:
        repo = _clone_or_open_repo()
        if sync_with_remote:
            _sync_branch(repo)

        if not repo.workdir:
            raise RuntimeError("Git repository does not have a working directory.")

        return repo.workdir.rstrip("/")


def commit_and_push_file(file_path: str, message: str) -> bool:
    with _repo_lock:
        repo = _clone_or_open_repo()

        workdir = repo.workdir
        if not workdir:
            raise RuntimeError("Git repository does not have a working directory.")

        absolute_file = Path(file_path).resolve()
        relative_path = absolute_file.relative_to(Path(workdir).resolve())

        index = repo.index
        index.add(str(relative_path))
        index.write()

        tree_oid = index.write_tree()

        parents: list[pygit2.Oid] = []
        if not repo.head_is_unborn:
            head_commit = repo[repo.head.target]
            if not isinstance(head_commit, pygit2.Commit):
                raise TypeError("HEAD does not point to a commit.")
            head_commit_obj = cast(pygit2.Commit, head_commit)
            parents = [head_commit_obj.id]
            if head_commit_obj.tree_id == tree_oid:
                return False

        signature = pygit2.Signature(get_git_author_name(), get_git_author_email())
        repo.create_commit(
            "HEAD",
            signature,
            signature,
            message,
            tree_oid,
            parents,
        )

        callbacks = _build_callbacks()
        branch = get_git_branch()
        push_ref = f"refs/heads/{branch}:refs/heads/{branch}"
        repo.remotes["origin"].push([push_ref], callbacks=callbacks)
        return True

