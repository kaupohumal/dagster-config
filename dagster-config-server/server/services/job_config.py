from __future__ import annotations

from typing import Any

from .assets import (
    find_asset_by_module_and_entry_index,
    find_asset_by_module,
    find_resource_by_type,
    key_value_list_to_dict,
    mappings_list_to_dict,
)
from .config import get_jobs_dir
from .yaml_loader import load_config, save_config


def _find_module_asset(
    data: dict[str, Any],
    module_name: str,
    module_index: int | None,
) -> dict[str, Any]:
    if module_index is None:
        asset = find_asset_by_module(data, module_name)
    else:
        asset = find_asset_by_module_and_entry_index(data, module_name, module_index)
    if not asset:
        if module_index is None:
            raise LookupError(f"No asset with module '{module_name}' found.")
        raise LookupError(
            f"No asset with module '{module_name}' found at index {module_index}."
        )
    return asset


def _update_http_get(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = _find_module_asset(data, "http_get", module_index)

    if "endpoint" in payload:
        asset.setdefault("params", {})["endpoint"] = payload.get("endpoint")

    if "params" in payload:
        new_params = key_value_list_to_dict(payload.get("params"), payload_name="params")
        asset.setdefault("params", {})["params"] = new_params



def _update_json_mapper(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = _find_module_asset(data, "json_mapper", module_index)

    if "mappings" in payload:
        new_mappings = mappings_list_to_dict(payload.get("mappings"))
        asset.setdefault("params", {})["mappings"] = new_mappings


def _update_write_to_csv(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = _find_module_asset(data, "write_to_csv", module_index)

    if "fileName" in payload:
        asset.setdefault("params", {})["file_name"] = payload.get("fileName")

    if "minioBucket" in payload:
        minio_bucket = payload.get("minioBucket")
        if minio_bucket is not None and not isinstance(minio_bucket, str):
            raise ValueError("minioBucket must be a string or null")
        params = asset.setdefault("params", {})
        minio_params = params.get("minio")
        if not isinstance(minio_params, dict):
            minio_params = {}
            params["minio"] = minio_params
        minio_params["bucket"] = "" if minio_bucket is None else minio_bucket.strip()

    if "minioHost" in payload or "minioAccessKey" in payload or "minioSecretKey" in payload:
        resource = find_resource_by_type(data, "MinIO")
        if not resource:
            raise LookupError("No resource with type 'MinIO' found.")
        resource_params = resource.setdefault("params", {})

        if "minioHost" in payload:
            minio_host = payload.get("minioHost")
            if minio_host is not None and not isinstance(minio_host, str):
                raise ValueError("minioHost must be a string or null")
            resource_params["host"] = "" if minio_host is None else minio_host.strip()

        if "minioAccessKey" in payload:
            minio_access_key = payload.get("minioAccessKey")
            if minio_access_key is not None and not isinstance(minio_access_key, str):
                raise ValueError("minioAccessKey must be a string or null")
            resource_params["access_key"] = "" if minio_access_key is None else minio_access_key.strip()

        if "minioSecretKey" in payload:
            minio_secret_key = payload.get("minioSecretKey")
            if minio_secret_key is not None and not isinstance(minio_secret_key, str):
                raise ValueError("minioSecretKey must be a string or null")
            resource_params["secret_key"] = "" if minio_secret_key is None else minio_secret_key.strip()


def _update_transform_to_arcgis_format(
    data: dict[str, Any], payload: dict[str, Any], module_index: int | None
) -> None:
    asset = _find_module_asset(data, "transform_to_arcgis_format", module_index)

    if "lat" in payload:
        asset.setdefault("params", {})["lat"] = payload.get("lat")

    if "lng" in payload:
        asset.setdefault("params", {})["lng"] = payload.get("lng")


def _update_send_to_arcgis(
    data: dict[str, Any], payload: dict[str, Any], module_index: int | None
) -> None:
    asset = _find_module_asset(data, "send_to_arcgis", module_index)

    if "layerName" in payload:
        asset.setdefault("params", {})["layer_name"] = payload.get("layerName")

    if "sublayerName" in payload:
        asset.setdefault("params", {})["sublayer_name"] = payload.get("sublayerName")

    if "featureServiceAddress" in payload or "arcgisToken" in payload:
        resource = find_resource_by_type(data, "ArcGIS")
        if not resource:
            raise LookupError("No resource with type 'ArcGIS' found.")
        resource_params = resource.setdefault("params", {})

        if "featureServiceAddress" in payload:
            resource_params["feature_service_address"] = payload.get("featureServiceAddress")

        if "arcgisToken" in payload:
            arcgis_token = payload.get("arcgisToken")
            if arcgis_token is not None and not isinstance(arcgis_token, str):
                raise ValueError("arcgisToken must be a string or null")
            resource_params["token"] = "" if arcgis_token is None else arcgis_token.strip()


def update_module_config(
    pipeline_name: str,
    module_name: str,
    payload: dict[str, Any],
    module_index: int | None = None,
) -> dict[str, Any]:

    if module_index is not None and (not isinstance(module_index, int) or module_index < 0):
        raise ValueError("module_index must be a non-negative integer")

    jobs_dir = get_jobs_dir()
    yaml_file = jobs_dir.rstrip("/") + "/" + pipeline_name + '.yaml'
    data = load_config(yaml_file)

    match module_name:
        case "http_get":
            _update_http_get(data, payload, module_index)
        case "json_mapper":
            _update_json_mapper(data, payload, module_index)
        case "write_to_csv":
            _update_write_to_csv(data, payload, module_index)
        case "transform_to_arcgis_format":
            _update_transform_to_arcgis_format(data, payload, module_index)
        case "send_to_arcgis":
            _update_send_to_arcgis(data, payload, module_index)
        case _:
            raise ValueError(f"Unsupported module_name: {module_name}")

    save_config(yaml_file, data)
    return {"ok": True}