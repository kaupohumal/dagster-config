from __future__ import annotations

from pathlib import Path

from .config import get_jobs_dir


def list_pipeline_names(dir_path: str | None = None) -> list[str]:
    """Return YAML pipeline names (filenames without extension) from a directory.

    Only regular files with a `.yaml` extension are included (case-insensitive).
    The returned list is sorted for stable output.
    """

    p = Path(dir_path or get_jobs_dir())
    if not p.exists():
        raise FileNotFoundError(f"Pipelines directory not found: {dir_path}")
    if not p.is_dir():
        raise NotADirectoryError(f"Pipelines directory is not a directory: {dir_path}")

    names: set[str] = set()
    for entry in p.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() != ".yaml":
            continue
        names.add(entry.stem)

    return sorted(names)

