from __future__ import annotations

import keyword
import re

# Dagster names may contain letters, numbers, and underscores (ASCII only).
_DAGSTER_NAME_RE = re.compile(r"^\w+$", re.ASCII)


def validate_pipeline_name(pipeline_name: str) -> str:
    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    normalized = pipeline_name.strip()

    if not _DAGSTER_NAME_RE.fullmatch(normalized):
        raise ValueError(
            "Invalid pipeline name. Use only letters, numbers, and underscores."
        )

    if keyword.iskeyword(normalized):
        raise ValueError("Invalid pipeline name. Python keywords are not allowed.")

    return normalized


