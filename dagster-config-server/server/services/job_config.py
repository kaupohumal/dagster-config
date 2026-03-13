from __future__ import annotations

from pathlib import Path
from typing import Any

from .assets import find_asset_by_module, mappings_list_to_dict
from .config import get_jobs_dir
from .git_repo import commit_and_push_file
from .yaml_loader import load_config, save_config


def _validate_pipeline_name(pipeline_name: str) -> str:
    if not isinstance(pipeline_name, str) or not pipeline_name.strip():
        raise ValueError("pipeline_name must be a non-empty string")

    name = pipeline_name.strip()
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid pipeline name")

    return name


def _update_http_get(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "http_get")
    if not asset:
        raise LookupError("No asset with module 'http_get' found.")

    params = asset.setdefault("params", {})
    nested_params = params.setdefault("params", {})

    if "endpoint" in payload:
        params["endpoint"] = payload.get("endpoint")

    if "eventType" in payload:
        nested_params["event_type"] = payload.get("eventType")

    if "pageSize" in payload:
        nested_params["page_size"] = int(payload.get("pageSize"))

    if "currentPage" in payload:
        nested_params["current_page"] = int(payload.get("currentPage"))



def _update_json_mapper(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "json_mapper")
    if not asset:
        raise LookupError("No asset with module 'json_mapper' found.")

    if "mappings" in payload:
        new_mappings = mappings_list_to_dict(payload.get("mappings"))
        asset.setdefault("params", {})["mappings"] = new_mappings


def _update_write_to_csv(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "write_to_csv")
    if not asset:
        raise LookupError("No asset with module 'write_to_csv' found.")

    if "fileName" in payload:
        asset.setdefault("params", {})["file_name"] = payload.get("fileName")


def update_module_config(pipeline_name: str, module_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    pipeline = _validate_pipeline_name(pipeline_name)
    jobs_dir = get_jobs_dir()
    yaml_file = str(Path(jobs_dir) / f"{pipeline}.yaml")
    data = load_config(yaml_file)

    match module_name:
        case "http_get":
            _update_http_get(data, payload)
        case "json_mapper":
            _update_json_mapper(data, payload)
        case "write_to_csv":
            _update_write_to_csv(data, payload)
        case _:
            raise ValueError(f"Unsupported module_name: {module_name}")

    save_config(yaml_file, data)

    commit_message = payload.get("commitMessage")
    if not isinstance(commit_message, str) or not commit_message.strip():
        commit_message = f"Update {module_name} config for pipeline {pipeline}"

    pushed = commit_and_push_file(yaml_file, commit_message.strip())
    return {"ok": True, "committed": pushed}
