from __future__ import annotations

import os
from pathlib import Path


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"{name} environment variable is not set.")
    return value


def get_git_repo_url() -> str:
    return _get_required_env("GIT_REPO_URL")


def get_git_branch() -> str:
    return os.environ.get("GIT_BRANCH", "main")


def get_repo_workdir() -> str:
    return os.environ.get("REPO_WORKDIR", "/tmp/dagster-jobs-repo")


def get_jobs_subdir() -> str:
    return os.environ.get("JOBS_SUBDIR", "").strip("/")


def get_git_author_name() -> str:
    return os.environ.get("GIT_AUTHOR_NAME", "Dagster Config UI")


def get_git_author_email() -> str:
    return os.environ.get("GIT_AUTHOR_EMAIL", "dagster-config-ui@local")


def get_git_username() -> str:
    return os.environ.get("GIT_USERNAME", "git")


def get_git_token() -> str | None:
    token = os.environ.get("GIT_TOKEN")
    return token if token else None


def get_jobs_dir() -> str:
    from .git_repo import ensure_repo_ready

    repo_dir = Path(ensure_repo_ready(sync_with_remote=True))
    jobs_subdir = get_jobs_subdir()
    jobs_dir = repo_dir / jobs_subdir if jobs_subdir else repo_dir
    if not jobs_dir.exists():
        raise FileNotFoundError(f"Jobs directory not found in repo: {jobs_dir}")
    if not jobs_dir.is_dir():
        raise NotADirectoryError(f"Jobs path is not a directory: {jobs_dir}")
    return str(jobs_dir)

