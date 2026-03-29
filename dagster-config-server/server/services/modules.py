from __future__ import annotations

from pathlib import Path
from typing import Any

from .assets import dict_to_pair_list, find_asset_by_module
from .config import get_jobs_dir
from .yaml_loader import load_config


def list_module_names_for_pipeline(pipeline_name: str, pipelines_dir: str | None = None) -> list[str]:

    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    name = pipeline_name.strip()
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid pipeline name")

    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
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


def _validate_pipeline_name(pipeline_name: str) -> str:
    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    name = pipeline_name.strip()
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid pipeline name")

    return name


def get_http_get_data(pipeline_name: str, pipelines_dir: str | None = None) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_asset_by_module(config, "http_get")
    if not asset:
        raise LookupError("No asset with module 'http_get' found.")

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    endpoint = params.get("endpoint")

    nested_params = params.get("params")
    params_list = dict_to_pair_list(
        nested_params,
        key_field="key",
        value_field="value",
    )

    return {
        "module": "http_get",
        "endpoint": endpoint,
        "params": params_list,
    }


def get_json_mapper_data(pipeline_name: str, pipelines_dir: str | None = None) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_asset_by_module(config, "json_mapper")
    if not asset:
        raise LookupError("No asset with module 'json_mapper' found.")

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    mappings_list = dict_to_pair_list(
        params.get("mappings"),
        key_field="key",
        value_field="value",
    )

    return {
        "module": "json_mapper",
        "mappings": mappings_list,
    }


def get_write_to_csv_data(pipeline_name: str, pipelines_dir: str | None = None) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_asset_by_module(config, "write_to_csv")
    if not asset:
        raise LookupError("No asset with module 'write_to_csv' found.")

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    file_name = params.get("file_name")

    return {
        "module": "write_to_csv",
        "fileName": file_name,
    }


def get_module_data(pipeline_name: str, module_name: str) -> dict[str, Any]:

    match module_name:
        case "http_get":
            return get_http_get_data(pipeline_name)
        case "json_mapper":
            return get_json_mapper_data(pipeline_name)
        case "write_to_csv":
            return get_write_to_csv_data(pipeline_name)
        case _:
            raise ValueError(f"Unsupported module_name: {module_name}")
