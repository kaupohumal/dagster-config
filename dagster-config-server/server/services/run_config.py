from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .assets import find_resource_by_type
from .config import get_jobs_dir
from .modules import pipeline_requires_resource_type
from .yaml_loader import load_config


def _load_pipeline_config(pipeline_name: str) -> dict[str, Any]:
    yaml_path = Path(get_jobs_dir()) / f"{pipeline_name}.yaml"
    return load_config(str(yaml_path))


def _resolve_resource_params(
    config: dict[str, Any],
    resource_type: str,
) -> tuple[str, dict[str, Any]]:
    resource = find_resource_by_type(config, resource_type)
    if not resource:
        raise LookupError(f"No resource with type '{resource_type}' found.")

    resource_name = resource.get("name") if isinstance(resource, dict) else None
    if not isinstance(resource_name, str) or not resource_name.strip():
        raise LookupError(f"{resource_type} resource must define a non-empty 'name'.")

    params = resource.get("params") if isinstance(resource, dict) else None
    resource_params = dict(params) if isinstance(params, dict) else {}
    return resource_name.strip(), resource_params


def _merge_resource_config(
    merged_config: dict[str, Any],
    resource_name: str,
    yaml_resource_params: dict[str, Any],
) -> dict[str, Any]:
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

    merged_resource_config = dict(yaml_resource_params)
    merged_resource_config.update(resource_config)
    resource_entry["config"] = merged_resource_config
    return merged_resource_config


def apply_arcgis_resource_config(
    pipeline_name: str,
    run_config_data: dict[str, Any] | None,
    feature_service_address_override: str | None = None,
) -> dict[str, Any]:
    pipeline_config = _load_pipeline_config(pipeline_name)
    merged_config = deepcopy(run_config_data) if run_config_data is not None else {}

    if not pipeline_requires_resource_type(pipeline_config, "ArcGIS"):
        return merged_config

    resource_name, yaml_resource_params = _resolve_resource_params(pipeline_config, "ArcGIS")
    merged_resource_config = _merge_resource_config(
        merged_config,
        resource_name,
        yaml_resource_params,
    )

    yaml_token = yaml_resource_params.get("token")
    merged_token = merged_resource_config.get("token")
    if isinstance(yaml_token, str) and yaml_token.strip():
        # Keep the persisted pipeline token if run config provided an empty token.
        if not isinstance(merged_token, str) or not merged_token.strip():
            merged_resource_config["token"] = yaml_token

    if isinstance(feature_service_address_override, str):
        normalized_override = feature_service_address_override.strip()
        if normalized_override:
            merged_resource_config["feature_service_address"] = normalized_override

    return merged_config


def apply_minio_resource_config(
    pipeline_name: str,
    run_config_data: dict[str, Any] | None,
) -> dict[str, Any]:
    pipeline_config = _load_pipeline_config(pipeline_name)
    merged_config = deepcopy(run_config_data) if run_config_data is not None else {}

    if not pipeline_requires_resource_type(pipeline_config, "MinIO"):
        return merged_config

    resource_name, yaml_resource_params = _resolve_resource_params(pipeline_config, "MinIO")
    merged_resource_config = _merge_resource_config(
        merged_config,
        resource_name,
        yaml_resource_params,
    )

    yaml_secret_key = yaml_resource_params.get("secret_key")
    merged_secret_key = merged_resource_config.get("secret_key")
    if isinstance(yaml_secret_key, str) and yaml_secret_key.strip():
        if not isinstance(merged_secret_key, str) or not merged_secret_key.strip():
            merged_resource_config["secret_key"] = yaml_secret_key

    return merged_config


