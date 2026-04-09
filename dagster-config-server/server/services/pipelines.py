from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .config import get_jobs_dir
from .yaml_loader import load_config, save_config


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


def _validate_pipeline_name(pipeline_name: str) -> str:
    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    name = pipeline_name.strip()
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid pipeline name")

    return name


def _get_pipeline_path(pipeline_name: str, pipelines_dir: str | None = None) -> Path:
    return Path(pipelines_dir or get_jobs_dir()) / f"{pipeline_name}.yaml"


def _get_primary_job(config: dict[str, Any]) -> dict[str, Any]:
    jobs = config.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise LookupError("Pipeline has no jobs.")

    for job in jobs:
        if isinstance(job, dict):
            return job

    raise LookupError("Pipeline has no valid jobs.")


def _validate_cron_field(field: str, minimum: int, maximum: int, field_name: str) -> None:
    if field == "*":
        return

    for part in field.split(","):
        token = part.strip()
        if not token:
            raise ValueError(f"Invalid cron {field_name}: empty token")

        if "/" in token:
            base, step = token.split("/", 1)
            if not step.isdigit() or int(step) <= 0:
                raise ValueError(f"Invalid cron {field_name}: invalid step '{token}'")
            if base == "*":
                continue
            token = base

        if token == "*":
            continue

        if "-" in token:
            start, end = token.split("-", 1)
            if not start.isdigit() or not end.isdigit():
                raise ValueError(f"Invalid cron {field_name}: invalid range '{token}'")
            start_i = int(start)
            end_i = int(end)
            if start_i > end_i:
                raise ValueError(f"Invalid cron {field_name}: descending range '{token}'")
            if start_i < minimum or end_i > maximum:
                raise ValueError(
                    f"Invalid cron {field_name}: value outside {minimum}-{maximum}"
                )
            continue

        if not token.isdigit():
            raise ValueError(f"Invalid cron {field_name}: invalid token '{token}'")
        value = int(token)
        if value < minimum or value > maximum:
            raise ValueError(f"Invalid cron {field_name}: value outside {minimum}-{maximum}")


def _validate_cron_expression(cron: str) -> str:
    if not isinstance(cron, str) or not cron.strip():
        raise ValueError("cron must be a non-empty string")

    normalized = cron.strip()
    if not re.fullmatch(r"[0-9\*/,\-\s]+", normalized):
        raise ValueError("cron contains unsupported characters")

    parts = normalized.split()
    if len(parts) != 5:
        raise ValueError("cron must have exactly 5 fields")

    _validate_cron_field(parts[0], 0, 59, "minute")
    _validate_cron_field(parts[1], 0, 23, "hour")
    _validate_cron_field(parts[2], 1, 31, "day-of-month")
    _validate_cron_field(parts[3], 1, 12, "month")
    _validate_cron_field(parts[4], 0, 6, "day-of-week")

    return normalized


def get_pipeline_schedule(pipeline_name: str, pipelines_dir: str | None = None) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = _get_pipeline_path(name, pipelines_dir)
    config = load_config(str(yaml_path))
    job = _get_primary_job(config)

    schedule = job.get("schedule")
    if not isinstance(schedule, dict):
        return {"pipeline": name, "hasSchedule": False, "cron": None}

    cron = schedule.get("cron")
    if not isinstance(cron, str) or not cron.strip():
        return {"pipeline": name, "hasSchedule": False, "cron": None}

    return {"pipeline": name, "hasSchedule": True, "cron": cron.strip()}


def set_pipeline_schedule(
    pipeline_name: str,
    cron: str | None,
    pipelines_dir: str | None = None,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = _get_pipeline_path(name, pipelines_dir)
    config = load_config(str(yaml_path))
    job = _get_primary_job(config)

    normalized_cron: str | None = None
    if cron is not None:
        if not isinstance(cron, str):
            raise ValueError("cron must be a string or null")
        if cron.strip():
            normalized_cron = _validate_cron_expression(cron)

    if normalized_cron is None:
        job.pop("schedule", None)
    else:
        job["schedule"] = {"cron": normalized_cron}

    save_config(str(yaml_path), config)
    return {
        "ok": True,
        "pipeline": name,
        "hasSchedule": normalized_cron is not None,
        "cron": normalized_cron,
    }


