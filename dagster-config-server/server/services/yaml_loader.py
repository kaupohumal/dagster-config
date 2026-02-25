from __future__ import annotations

import os
from typing import Any

import yaml


def load_config(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML file not found: {path}")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_config(path: str, data: dict[str, Any]) -> None:
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
