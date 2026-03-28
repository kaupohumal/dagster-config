from __future__ import annotations

from typing import Any

from .assets import find_asset_by_module, mappings_list_to_dict
from .config import get_jobs_dir
from .yaml_loader import load_config, save_config


def _update_http_get(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "http_get")
    if not asset:
        raise LookupError("No asset with module 'http_get' found.")

    if "endpoint" in payload:
        asset.setdefault("params", {})["endpoint"] = payload.get("endpoint")

    if "eventType" in payload:
        asset.setdefault("params", {})["params"]["event_type"] = payload.get("eventType")

    if "pageSize" in payload:
        asset.setdefault("params", {})["params"]["page_size"] = int(payload.get("pageSize"))

    if "currentPage" in payload:
        asset.setdefault("params", {})["params"]["current_page"] = int(payload.get("currentPage"))



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

    jobs_dir = get_jobs_dir()
    yaml_file = jobs_dir.rstrip("/") + "/" + pipeline_name + '.yaml'
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
    return {"ok": True}