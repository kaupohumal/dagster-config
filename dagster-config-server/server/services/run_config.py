from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .assets import find_resource_by_type
from .config import get_jobs_dir
from .yaml_loader import load_config


def _load_pipeline_config(pipeline_name: str) -> dict[str, Any]:
    yaml_path = Path(get_jobs_dir()) / f"{pipeline_name}.yaml"
    return load_config(str(yaml_path))


def _resolve_arcgis_resource(config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    resource = find_resource_by_type(config, "ArcGIS")
    if not resource:
        raise LookupError("No resource with type 'ArcGIS' found.")

    resource_name = resource.get("name") if isinstance(resource, dict) else None
    if not isinstance(resource_name, str) or not resource_name.strip():
        raise LookupError("ArcGIS resource must define a non-empty 'name'.")

    params = resource.get("params") if isinstance(resource, dict) else None
    resource_params = dict(params) if isinstance(params, dict) else {}
    return resource_name.strip(), resource_params


def _pipeline_requires_arcgis(config: dict[str, Any]) -> bool:
    for job in config.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for asset in job.get("assets", []) or []:
            if not isinstance(asset, dict):
                continue
            module_name = asset.get("module")
            if isinstance(module_name, str) and module_name.strip() == "send_to_arcgis":
                return True
    return False


def apply_arcgis_resource_config(
    pipeline_name: str,
    run_config_data: dict[str, Any] | None,
    feature_service_address_override: str | None = None,
) -> dict[str, Any]:
    pipeline_config = _load_pipeline_config(pipeline_name)
    merged_config = deepcopy(run_config_data) if run_config_data is not None else {}

    if not _pipeline_requires_arcgis(pipeline_config):
        return merged_config

    resource_name, yaml_resource_params = _resolve_arcgis_resource(pipeline_config)

    resources = merged_config.setdefault("resources", {})
    if not isinstance(resources, dict):
        raise ValueError("runConfigData.resources must be an object.")

    resource_entry = resources.setdefault(resource_name, {})
    if not isinstance(resource_entry, dict):
        raise ValueError(
            f"runConfigData.resources.{resource_name} must be an object."
        )

    resource_config = resource_entry.setdefault("config", {})
    if not isinstance(resource_config, dict):
        raise ValueError(
            f"runConfigData.resources.{resource_name}.config must be an object."
        )

    # Start from YAML resource params so required values (e.g. token) remain present.
    merged_resource_config = dict(yaml_resource_params)
    merged_resource_config.update(resource_config)

    if isinstance(feature_service_address_override, str):
        normalized_override = feature_service_address_override.strip()
        if normalized_override:
            merged_resource_config["feature_service_address"] = normalized_override

    resource_entry["config"] = merged_resource_config
    return merged_config

