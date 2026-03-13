from __future__ import annotations

from pathlib import Path

from .config import get_jobs_dir


def list_pipeline_names_from_repo() -> list[str]:
    return list_pipeline_names(get_jobs_dir())


def list_pipeline_names(dir_path: str | None = None) -> list[str]:

    resolved_dir = dir_path or get_jobs_dir()
    p = Path(resolved_dir)
    if not p.exists():
        raise FileNotFoundError(f"Pipelines directory not found: {resolved_dir}")
    if not p.is_dir():
        raise NotADirectoryError(f"Pipelines directory is not a directory: {resolved_dir}")

    names: set[str] = set()
    for entry in p.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() != ".yaml":
            continue
        names.add(entry.stem)

    return sorted(names)

