from __future__ import annotations

from pathlib import Path
from typing import Any

from .pipelines import PIPELINES_DIR
from .yaml_loader import load_config


def list_module_names_for_pipeline(pipeline_name: str, pipelines_dir: str = PIPELINES_DIR) -> list[str]:
    """Return all module names from the given pipeline YAML.

    Args:
        pipeline_name: YAML name without extension (e.g. "bus_validations").
        pipelines_dir: Directory containing YAML files.

    Returns:
        Sorted list of unique module names found under config.jobs[*].assets[*].module.

    Raises:
        ValueError: invalid pipeline_name.
        FileNotFoundError: YAML file doesn't exist.
    """

    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    # Prevent path traversal like "../../etc/passwd".
    name = pipeline_name.strip()
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid pipeline name")

    yaml_path = str(Path(pipelines_dir) / f"{name}.yaml")
    config = load_config(yaml_path)

    modules: set[str] = set()
    for job in config.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for asset in job.get("assets", []) or []:
            if not isinstance(asset, dict):
                continue
            module = asset.get("module")
            if isinstance(module, str) and module.strip():
                modules.add(module)

    return sorted(modules)

