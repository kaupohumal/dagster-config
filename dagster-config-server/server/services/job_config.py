from __future__ import annotations

from typing import Any

from .assets import (
    find_resource_by_type,
    key_value_list_to_dict,
    mappings_list_to_dict,
    find_module_asset_or_error,
    validate_module_index,
)
from .config import get_jobs_dir
from .yaml_loader import load_config, save_config


def _string_field(data: dict[str, Any], key: str, *, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{context}.{key} must be a string")
    return value


def _normalize_http_get_auth(
    auth_payload: object,
    existing_auth: object,
) -> dict[str, dict[str, str]]:
    if auth_payload is None:
        return {}
    if not isinstance(auth_payload, dict):
        raise ValueError("auth must be an object")

    supported_modes = ("basic_auth", "bearer_token", "api_key")
    selected_modes: list[str] = [mode for mode in supported_modes if auth_payload.get(mode) is not None]

    if len(selected_modes) > 1:
        raise ValueError("auth must define exactly one auth mode")
    if len(selected_modes) == 0:
        return {}

    mode = selected_modes[0]
    raw_mode_data = auth_payload.get(mode)
    if not isinstance(raw_mode_data, dict):
        raise ValueError(f"auth.{mode} must be an object")

    previous_mode_data: dict[str, Any] = {}
    if isinstance(existing_auth, dict):
        existing_mode_data = existing_auth.get(mode)
        if isinstance(existing_mode_data, dict):
            previous_mode_data = existing_mode_data

    if mode == "basic_auth":
        username = _string_field(raw_mode_data, "username", context="auth.basic_auth")
        password = raw_mode_data.get("password")
        if password is None:
            password_value = previous_mode_data.get("password")
        else:
            if not isinstance(password, str):
                raise ValueError("auth.basic_auth.password must be a string")
            password_value = password

        if not isinstance(password_value, str):
            password_value = ""
        return {"basic_auth": {"username": username, "password": password_value}}

    if mode == "bearer_token":
        token = raw_mode_data.get("token")
        if token is None:
            token_value = previous_mode_data.get("token")
        else:
            if not isinstance(token, str):
                raise ValueError("auth.bearer_token.token must be a string")
            token_value = token

        if not isinstance(token_value, str):
            token_value = ""
        return {"bearer_token": {"token": token_value}}

    key_name = _string_field(raw_mode_data, "key_name", context="auth.api_key")
    key = raw_mode_data.get("key")
    if key is None:
        key_value = previous_mode_data.get("key")
    else:
        if not isinstance(key, str):
            raise ValueError("auth.api_key.key must be a string")
        key_value = key

    if not isinstance(key_value, str):
        key_value = ""
    return {"api_key": {"key": key_value, "key_name": key_name}}


def _update_http_get(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = find_module_asset_or_error(data, "http_get", module_index)
    params = asset.setdefault("params", {})

    if "endpoint" in payload:
        params["endpoint"] = payload.get("endpoint")

    if "params" in payload:
        new_params = key_value_list_to_dict(payload.get("params"), payload_name="params")
        params["params"] = new_params

    if "auth" in payload:
        auth = _normalize_http_get_auth(payload.get("auth"), params.get("auth"))
        if auth:
            params["auth"] = auth
        else:
            params.pop("auth", None)



def _update_json_mapper(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = find_module_asset_or_error(data, "json_mapper", module_index)

    if "mappings" in payload:
        new_mappings = mappings_list_to_dict(payload.get("mappings"))
        asset.setdefault("params", {})["mappings"] = new_mappings


def _update_write_to_csv(data: dict[str, Any], payload: dict[str, Any], module_index: int | None) -> None:
    asset = find_module_asset_or_error(data, "write_to_csv", module_index)

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
    asset = find_module_asset_or_error(data, "transform_to_arcgis_format", module_index)

    if "lat" in payload:
        asset.setdefault("params", {})["lat"] = payload.get("lat")

    if "lng" in payload:
        asset.setdefault("params", {})["lng"] = payload.get("lng")


def _update_send_to_arcgis(
    data: dict[str, Any], payload: dict[str, Any], module_index: int | None
) -> None:
    asset = find_module_asset_or_error(data, "send_to_arcgis", module_index)

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
    validate_module_index(module_index)

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