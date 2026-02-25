from __future__ import annotations

from typing import Any


def find_asset_by_module(config: dict[str, Any], module_name: str) -> dict[str, Any] | None:

    for job in config.get("jobs", []) or []:
        for asset in job.get("assets", []) or []:
            if asset.get("module") == module_name:
                return asset
    return None


def mappings_list_to_dict(mappings_list: object) -> dict[str, str]:

    if mappings_list is None:
        raise ValueError("Missing 'mappings'.")
    if not isinstance(mappings_list, list):
        raise ValueError("'mappings' must be a list of {source,target} objects.")

    out: dict[str, str] = {}
    for i, item in enumerate(mappings_list):
        if not isinstance(item, dict):
            raise ValueError(f"mappings[{i}] must be an object.")
        source = item.get("source")
        target = item.get("target")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"mappings[{i}].source must be a non-empty string.")
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"mappings[{i}].target must be a non-empty string.")
        if target in out:
            raise ValueError(f"Duplicate target '{target}' in mappings.")
        out[target] = source

    return out
