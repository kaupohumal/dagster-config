from __future__ import annotations

from pathlib import Path

# Hardcoded for now. Later we can make this configurable via env/config.
PIPELINES_DIR = "/home/kaupo/kool/thesis/dagster/dagster-user-code/jobs"


def list_pipeline_names(dir_path: str = PIPELINES_DIR) -> list[str]:
    """Return YAML pipeline names (filenames without extension) from a directory.

    Only regular files with a `.yaml` extension are included (case-insensitive).
    The returned list is sorted for stable output.
    """

    p = Path(dir_path)
    if not p.exists():
        raise FileNotFoundError(f"Pipelines directory not found: {dir_path}")
    if not p.is_dir():
        raise NotADirectoryError(f"Pipelines directory is not a directory: {dir_path}")

    names: set[str] = set()
    for entry in p.iterdir():
        if not entry.is_file():
            continue
        # Only `.yaml` for now (as requested). Case-insensitive.
        if entry.suffix.lower() != ".yaml":
            continue
        names.add(entry.stem)

    return sorted(names)

