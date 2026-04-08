from __future__ import annotations

from typing import Any

from .assets import (
    find_asset_by_module,
    find_resource_by_type,
    key_value_list_to_dict,
    mappings_list_to_dict,
)
from .config import get_jobs_dir
from .yaml_loader import load_config, save_config


def _update_http_get(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "http_get")
    if not asset:
        raise LookupError("No asset with module 'http_get' found.")

    if "endpoint" in payload:
        asset.setdefault("params", {})["endpoint"] = payload.get("endpoint")

    if "params" in payload:
        new_params = key_value_list_to_dict(payload.get("params"), payload_name="params")
        asset.setdefault("params", {})["params"] = new_params



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


def _update_transform_to_arcgis_format(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "transform_to_arcgis_format")
    if not asset:
        raise LookupError("No asset with module 'transform_to_arcgis_format' found.")

    if "lat" in payload:
        asset.setdefault("params", {})["lat"] = payload.get("lat")

    if "lng" in payload:
        asset.setdefault("params", {})["lng"] = payload.get("lng")


def _update_send_to_arcgis(data: dict[str, Any], payload: dict[str, Any]) -> None:
    asset = find_asset_by_module(data, "send_to_arcgis")
    if not asset:
        raise LookupError("No asset with module 'send_to_arcgis' found.")

    if "layerName" in payload:
        asset.setdefault("params", {})["layer_name"] = payload.get("layerName")

    if "sublayerName" in payload:
        asset.setdefault("params", {})["sublayer_name"] = payload.get("sublayerName")

    if "featureServiceAddress" in payload:
        resource = find_resource_by_type(data, "ArcGIS")
        if not resource:
            raise LookupError("No resource with type 'ArcGIS' found.")
        resource.setdefault("params", {})["feature_service_address"] = payload.get(
            "featureServiceAddress"
        )


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
        case "transform_to_arcgis_format":
            _update_transform_to_arcgis_format(data, payload)
        case "send_to_arcgis":
            _update_send_to_arcgis(data, payload)
        case _:
            raise ValueError(f"Unsupported module_name: {module_name}")

    save_config(yaml_file, data)
    return {"ok": True}