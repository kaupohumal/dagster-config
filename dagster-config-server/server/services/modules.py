from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, TypedDict

from .assets import (
    dict_to_pair_list,
    find_resource_by_type,
    find_module_asset_or_error,
    validate_module_index,
)
from .config import get_jobs_dir
from .pipeline_name_validation import validate_pipeline_name
from .yaml_loader import load_config, save_config


class ModuleEntry(TypedDict):
    name: str
    asset: str | None
    ins: str | list[str] | dict[str, Any] | None
    index: int


class ModuleCatalogEntry(TypedDict):
    module: str
    label: str
    default_asset: str
    default_params: dict[str, Any]
    required_resources: list[str]


MODULE_CATALOG: dict[str, ModuleCatalogEntry] = {
    "http_get": {
        "module": "http_get",
        "label": "HTTP Get",
        "default_asset": "fetch_data",
        "default_params": {
            "endpoint": "",
            "params": {},
        },
        "required_resources": [],
    },
    "json_mapper": {
        "module": "json_mapper",
        "label": "JSON Mapper",
        "default_asset": "map_data",
        "default_params": {
            "mappings": {},
        },
        "required_resources": [],
    },
    "write_to_csv": {
        "module": "write_to_csv",
        "label": "Write To CSV",
        "default_asset": "write_csv",
        "default_params": {
            "file_name": "output.csv",
            "minio": {
                "bucket": "dagster-integration",
            },
        },
        "required_resources": ["MinIO"],
    },
    "transform_to_arcgis_format": {
        "module": "transform_to_arcgis_format",
        "label": "Transform To ArcGIS Format",
        "default_asset": "transform_arcgis",
        "default_params": {
            "lat": "lat",
            "lng": "lng",
        },
        "required_resources": [],
    },
    "send_to_arcgis": {
        "module": "send_to_arcgis",
        "label": "Send To ArcGIS",
        "default_asset": "send_arcgis",
        "default_params": {
            "layer_name": "",
            "sublayer_name": "",
        },
        "required_resources": ["ArcGIS"],
    },
}


def _list_module_entries_for_pipeline_config(config: dict[str, Any]) -> list[ModuleEntry]:
    entries: list[ModuleEntry] = []

    for job in config.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for asset in job.get("assets", []) or []:
            if not isinstance(asset, dict):
                continue
            module = asset.get("module")
            if not isinstance(module, str) or not module.strip():
                continue

            entries.append(
                {
                    "name": module.strip(),
                    "asset": asset.get("asset") if isinstance(asset.get("asset"), str) else None,
                    "ins": asset.get("ins"),
                    "index": len(entries),
                }
            )

    return entries


def _validate_module_name(module_name: str) -> str:
    if not isinstance(module_name, str) or not module_name.strip():
        raise ValueError("module_name must be a non-empty string")
    normalized = module_name.strip()
    if normalized not in MODULE_CATALOG:
        raise ValueError(f"Unsupported module_name: {module_name}")
    return normalized


def _get_assets(config: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for job in config.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for asset in job.get("assets", []) or []:
            if isinstance(asset, dict):
                assets.append(asset)
    return assets


def _ensure_arcgis_resource(config: dict[str, Any]) -> bool:
    if find_resource_by_type(config, "ArcGIS"):
        return False

    resources = config.get("resources")
    if not isinstance(resources, list):
        resources = []
        config["resources"] = resources

    resources.append(
        {
            "resource": "ArcGIS",
            "name": "arcGIS",
            "params": {
                "token": "",
                "feature_service_address": "",
            },
        }
    )
    return True


def _ensure_minio_resource(config: dict[str, Any]) -> bool:
    if find_resource_by_type(config, "MinIO"):
        return False

    resources = config.get("resources")
    if not isinstance(resources, list):
        resources = []
        config["resources"] = resources

    resources.append(
        {
            "resource": "MinIO",
            "name": "minio",
            "params": {
                "host": "",
                "access_key": "",
                "secret_key": "",
            },
        }
    )
    return True


RESOURCE_ENSURERS = {
    "ArcGIS": _ensure_arcgis_resource,
    "MinIO": _ensure_minio_resource,
}


def _ensure_required_resources_for_module(config: dict[str, Any], module_name: str) -> list[str]:
    added_resources: list[str] = []
    for resource_type in MODULE_CATALOG[module_name]["required_resources"]:
        ensure_fn = RESOURCE_ENSURERS.get(resource_type)
        if ensure_fn and ensure_fn(config):
            added_resources.append(resource_type)
    return added_resources


def pipeline_requires_resource_type(config: dict[str, Any], resource_type: str) -> bool:
    for asset in _get_assets(config):
        module_name = asset.get("module")
        if not isinstance(module_name, str):
            continue
        catalog_entry = MODULE_CATALOG.get(module_name.strip())
        if not catalog_entry:
            continue
        if resource_type in catalog_entry["required_resources"]:
            return True
    return False


def _remove_unused_resources(config: dict[str, Any], resource_types: set[str]) -> list[str]:
    resources = config.get("resources")
    if not isinstance(resources, list):
        return []

    removed_resources: list[str] = []
    kept_resources: list[Any] = []

    for resource in resources:
        if not isinstance(resource, dict):
            kept_resources.append(resource)
            continue

        resource_type = resource.get("resource")
        if (
            isinstance(resource_type, str)
            and resource_type in resource_types
            and not pipeline_requires_resource_type(config, resource_type)
        ):
            removed_resources.append(resource_type)
            continue

        kept_resources.append(resource)

    config["resources"] = kept_resources
    return sorted(set(removed_resources))


def _module_params_with_defaults(module_name: str, raw_params: object) -> dict[str, Any]:
    defaults = MODULE_CATALOG[module_name]["default_params"]
    params = deepcopy(defaults)
    if isinstance(raw_params, dict):
        params.update(raw_params)
    return params


def _normalize_http_get_auth(auth: object) -> dict[str, dict[str, Any]]:
    if not isinstance(auth, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}

    api_key = auth.get("api_key")
    if isinstance(api_key, dict):
        key_name = api_key.get("key_name")
        key = api_key.get("key")
        if isinstance(key_name, str):
            normalized["api_key"] = {
                "key_name": key_name,
                "keySet": isinstance(key, str) and bool(key.strip()),
            }

    basic_auth = auth.get("basic_auth")
    if isinstance(basic_auth, dict):
        username = basic_auth.get("username")
        password = basic_auth.get("password")
        if isinstance(username, str):
            normalized["basic_auth"] = {
                "username": username,
                "passwordSet": isinstance(password, str) and bool(password.strip()),
            }

    bearer_token = auth.get("bearer_token")
    if isinstance(bearer_token, dict):
        token = bearer_token.get("token")
        normalized["bearer_token"] = {
            "tokenSet": isinstance(token, str) and bool(token.strip()),
        }

    # Keep only one auth mode in deterministic order if malformed YAML contains several.
    for mode in ("basic_auth", "bearer_token", "api_key"):
        if mode in normalized:
            return {mode: normalized[mode]}

    return {}


def _validate_asset_index(asset_index: int) -> int:
    if not isinstance(asset_index, int) or asset_index < 0:
        raise ValueError("asset_index must be a non-negative integer")
    return asset_index


def _is_module_asset(asset: object) -> bool:
    if not isinstance(asset, dict):
        return False
    module_name = asset.get("module")
    return isinstance(module_name, str) and bool(module_name.strip())


def _get_primary_assets(config: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = config.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise LookupError("Pipeline has no jobs.")

    for job in jobs:
        if not isinstance(job, dict):
            continue
        assets = job.get("assets")
        if not isinstance(assets, list):
            assets = []
            job["assets"] = assets
        return assets

    raise LookupError("Pipeline has no valid jobs.")


def _module_assets_count(assets: list[dict[str, Any]]) -> int:
    return sum(1 for asset in assets if _is_module_asset(asset))


def _resolve_raw_index_for_module_entry(assets: list[dict[str, Any]], module_index: int) -> int:
    current_index = 0
    for raw_index, asset in enumerate(assets):
        if not _is_module_asset(asset):
            continue
        if current_index == module_index:
            return raw_index
        current_index += 1
    raise LookupError(f"No asset found at index {module_index}")


def _resolve_raw_insert_index(assets: list[dict[str, Any]], insert_index: int) -> int:
    current_index = 0
    for raw_index, asset in enumerate(assets):
        if not _is_module_asset(asset):
            continue
        if current_index == insert_index:
            return raw_index
        current_index += 1
    if current_index == insert_index:
        return len(assets)
    raise LookupError(f"Invalid insert index {insert_index}")


def _validate_linear_pipeline_assets(assets: list[dict[str, Any]]) -> None:
    for asset in assets:
        if not _is_module_asset(asset):
            continue
        ins = asset.get("ins")
        if isinstance(ins, (list, dict)):
            raise ValueError("Add/remove modules is supported only for linear pipelines.")


def _rewire_linear_inputs(assets: list[dict[str, Any]]) -> None:
    module_assets = [asset for asset in assets if _is_module_asset(asset)]
    for index, asset in enumerate(module_assets):
        if index == 0:
            asset.pop("ins", None)
            continue

        prev_asset_name = module_assets[index - 1].get("asset")
        if isinstance(prev_asset_name, str) and prev_asset_name.strip():
            asset["ins"] = prev_asset_name.strip()
        else:
            asset.pop("ins", None)


def _generate_unique_asset_name(assets: list[dict[str, Any]], base_name: str) -> str:
    existing_names = {
        asset_name.strip()
        for asset in assets
        for asset_name in [asset.get("asset") if isinstance(asset, dict) else None]
        if isinstance(asset_name, str) and asset_name.strip()
    }

    candidate = base_name.strip() or "asset"
    suffix = 1
    while candidate in existing_names:
        suffix += 1
        candidate = f"{base_name}_{suffix}"
    return candidate


def list_module_catalog() -> list[ModuleCatalogEntry]:
    return [
        MODULE_CATALOG[module_name]
        for module_name in (
            "http_get",
            "json_mapper",
            "write_to_csv",
            "transform_to_arcgis_format",
            "send_to_arcgis",
        )
    ]


def list_module_names_for_pipeline(pipeline_name: str, pipelines_dir: str | None = None) -> list[str]:
    name = _validate_pipeline_name(pipeline_name)

    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    ordered_modules: list[str] = []
    seen_modules: set[str] = set()
    for entry in _list_module_entries_for_pipeline_config(config):
        module_name = entry["name"]
        if module_name in seen_modules:
            continue
        ordered_modules.append(module_name)
        seen_modules.add(module_name)

    return ordered_modules


def list_module_entries_for_pipeline(
    pipeline_name: str, pipelines_dir: str | None = None
) -> list[ModuleEntry]:
    name = _validate_pipeline_name(pipeline_name)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)
    return _list_module_entries_for_pipeline_config(config)


def _validate_pipeline_name(pipeline_name: str) -> str:
    return validate_pipeline_name(pipeline_name)


def create_pipeline_from_modules(
    pipeline_name: str,
    module_specs: object,
    pipelines_dir: str | None = None,
    job_name: str | None = None,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    if not isinstance(module_specs, list) or len(module_specs) == 0:
        raise ValueError("modules must be a non-empty list")

    normalized_specs: list[dict[str, Any]] = []
    for i, spec in enumerate(module_specs):
        if isinstance(spec, str):
            module_name = _validate_module_name(spec)
            normalized_specs.append({"module": module_name})
            continue

        if not isinstance(spec, dict):
            raise ValueError(f"modules[{i}] must be a string or object")

        raw_module = spec.get("module")
        module_name = _validate_module_name(raw_module if isinstance(raw_module, str) else "")
        normalized_specs.append(spec | {"module": module_name})

    assets: list[dict[str, Any]] = []
    required_resources: set[str] = set()

    for i, spec in enumerate(normalized_specs):
        module_name = spec["module"]
        catalog_entry = MODULE_CATALOG[module_name]
        asset_name = spec.get("asset")
        if not isinstance(asset_name, str) or not asset_name.strip():
            asset_name = f"{catalog_entry['default_asset']}_{i + 1}"

        asset_data: dict[str, Any] = {
            "asset": asset_name.strip(),
            "module": module_name,
            "params": _module_params_with_defaults(module_name, spec.get("params")),
        }

        if i > 0:
            asset_data["ins"] = assets[i - 1]["asset"]

        group = spec.get("group")
        if isinstance(group, str) and group.strip():
            asset_data["group"] = group.strip()

        assets.append(asset_data)

        required_resources.update(catalog_entry["required_resources"])

    config: dict[str, Any] = {
        "jobs": [
            {
                "job": job_name.strip() if isinstance(job_name, str) and job_name.strip() else name,
                "assets": assets,
            }
        ]
    }

    for resource_type in required_resources:
        ensure_fn = RESOURCE_ENSURERS.get(resource_type)
        if ensure_fn:
            ensure_fn(config)

    yaml_path = Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml"
    if yaml_path.exists():
        raise FileExistsError(f"Pipeline already exists: {name}")

    save_config(str(yaml_path), config)
    return {
        "ok": True,
        "pipeline": name,
        "created": True,
        "moduleCount": len(assets),
    }


def swap_module_for_pipeline_asset(
    pipeline_name: str,
    asset_index: int,
    target_module_name: str,
    pipelines_dir: str | None = None,
    preserve_compatible_params: bool = True,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    index = _validate_asset_index(asset_index)
    target_module = _validate_module_name(target_module_name)

    yaml_path = Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml"
    config = load_config(str(yaml_path))
    assets = _get_assets(config)

    if index >= len(assets):
        raise LookupError(f"No asset found at index {index}")

    asset = assets[index]
    current_module = asset.get("module")
    if not isinstance(current_module, str) or not current_module.strip():
        raise LookupError(f"Asset at index {index} has no valid module")
    current_module = current_module.strip()

    if current_module == target_module:
        return {
            "ok": True,
            "changed": False,
            "assetIndex": index,
            "module": target_module,
            "message": "Asset already uses the requested module.",
        }

    new_params = deepcopy(MODULE_CATALOG[target_module]["default_params"])
    previous_params = asset.get("params")
    if preserve_compatible_params and isinstance(previous_params, dict):
        for key in list(new_params.keys()):
            if key in previous_params:
                new_params[key] = previous_params[key]

    diagnostics = {
        "paramsRemoved": sorted(
            [
                key
                for key in (previous_params.keys() if isinstance(previous_params, dict) else [])
                if key not in new_params
            ]
        ),
        "paramsAdded": sorted([key for key in new_params if not isinstance(previous_params, dict) or key not in previous_params]),
        "addedResources": [],
    }

    asset["module"] = target_module
    if new_params:
        asset["params"] = new_params
    elif "params" in asset:
        del asset["params"]

    diagnostics["addedResources"].extend(
        _ensure_required_resources_for_module(config, target_module)
    )

    save_config(str(yaml_path), config)

    return {
        "ok": True,
        "changed": True,
        "assetIndex": index,
        "previousModule": current_module,
        "module": target_module,
        "diagnostics": diagnostics,
    }


def add_module_to_pipeline(
    pipeline_name: str,
    target_module_name: str,
    insert_index: int,
    pipelines_dir: str | None = None,
    asset_name: str | None = None,
    group: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    target_module = _validate_module_name(target_module_name)
    if not isinstance(insert_index, int) or insert_index < 0:
        raise ValueError("insert_index must be a non-negative integer")
    if params is not None and not isinstance(params, dict):
        raise ValueError("params must be an object")

    yaml_path = Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml"
    config = load_config(str(yaml_path))
    assets = _get_primary_assets(config)
    _validate_linear_pipeline_assets(assets)

    module_count = _module_assets_count(assets)
    if insert_index > module_count:
        raise LookupError(f"Invalid insert index {insert_index}")

    raw_insert_index = _resolve_raw_insert_index(assets, insert_index)
    default_asset_name = MODULE_CATALOG[target_module]["default_asset"]
    resolved_asset_name = (
        asset_name.strip()
        if isinstance(asset_name, str) and asset_name.strip()
        else _generate_unique_asset_name(assets, default_asset_name)
    )

    new_asset: dict[str, Any] = {
        "asset": resolved_asset_name,
        "module": target_module,
        "params": _module_params_with_defaults(target_module, params),
    }
    if isinstance(group, str) and group.strip():
        new_asset["group"] = group.strip()

    assets.insert(raw_insert_index, new_asset)
    _rewire_linear_inputs(assets)

    added_resources = _ensure_required_resources_for_module(config, target_module)

    save_config(str(yaml_path), config)
    return {
        "ok": True,
        "insertedIndex": insert_index,
        "module": target_module,
        "asset": resolved_asset_name,
        "addedResources": added_resources,
    }


def remove_module_from_pipeline(
    pipeline_name: str,
    asset_index: int,
    pipelines_dir: str | None = None,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    index = _validate_asset_index(asset_index)

    yaml_path = Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml"
    config = load_config(str(yaml_path))
    assets = _get_primary_assets(config)
    _validate_linear_pipeline_assets(assets)

    raw_remove_index = _resolve_raw_index_for_module_entry(assets, index)
    removed_asset = assets.pop(raw_remove_index)
    _rewire_linear_inputs(assets)

    removed_resources: list[str] = []
    removed_module_name = removed_asset.get("module")
    if isinstance(removed_module_name, str):
        catalog_entry = MODULE_CATALOG.get(removed_module_name.strip())
        if catalog_entry:
            removed_resources = _remove_unused_resources(
                config,
                set(catalog_entry["required_resources"]),
            )

    save_config(str(yaml_path), config)
    return {
        "ok": True,
        "removedIndex": index,
        "module": removed_asset.get("module"),
        "asset": removed_asset.get("asset"),
        "removedResources": removed_resources,
    }


def get_http_get_data(
    pipeline_name: str, pipelines_dir: str | None = None, module_index: int | None = None
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    validate_module_index(module_index)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_module_asset_or_error(config, "http_get", module_index)

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
    auth = _normalize_http_get_auth(params.get("auth"))

    return {
        "module": "http_get",
        "endpoint": endpoint,
        "params": params_list,
        "auth": auth,
    }


def get_json_mapper_data(
    pipeline_name: str, pipelines_dir: str | None = None, module_index: int | None = None
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    validate_module_index(module_index)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_module_asset_or_error(config, "json_mapper", module_index)

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


def get_write_to_csv_data(
    pipeline_name: str, pipelines_dir: str | None = None, module_index: int | None = None
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    validate_module_index(module_index)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_module_asset_or_error(config, "write_to_csv", module_index)

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    file_name = params.get("file_name")
    minio_params = params.get("minio") if isinstance(params.get("minio"), dict) else {}
    resource = find_resource_by_type(config, "MinIO")
    resource_params = resource.get("params") if isinstance(resource, dict) else None
    if not isinstance(resource_params, dict):
        resource_params = {}

    secret_key = resource_params.get("secret_key")
    secret_key_set = isinstance(secret_key, str) and bool(secret_key.strip())

    return {
        "module": "write_to_csv",
        "fileName": file_name,
        "minioBucket": minio_params.get("bucket"),
        "minioHost": resource_params.get("host"),
        "minioAccessKey": resource_params.get("access_key"),
        "minioSecretKeySet": secret_key_set,
    }


def get_transform_to_arcgis_format_data(
    pipeline_name: str,
    pipelines_dir: str | None = None,
    module_index: int | None = None,
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    validate_module_index(module_index)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_module_asset_or_error(config, "transform_to_arcgis_format", module_index)

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    return {
        "module": "transform_to_arcgis_format",
        "lat": params.get("lat"),
        "lng": params.get("lng"),
    }


def get_send_to_arcgis_data(
    pipeline_name: str, pipelines_dir: str | None = None, module_index: int | None = None
) -> dict[str, Any]:
    name = _validate_pipeline_name(pipeline_name)
    validate_module_index(module_index)
    yaml_path = str(Path(pipelines_dir or get_jobs_dir()) / f"{name}.yaml")
    config = load_config(yaml_path)

    asset = find_module_asset_or_error(config, "send_to_arcgis", module_index)

    params = asset.get("params") if isinstance(asset, dict) else None
    if not isinstance(params, dict):
        params = {}

    resource = find_resource_by_type(config, "ArcGIS")
    resource_params = resource.get("params") if isinstance(resource, dict) else None
    if not isinstance(resource_params, dict):
        resource_params = {}

    token = resource_params.get("token")
    token_set = isinstance(token, str) and bool(token.strip())

    return {
        "module": "send_to_arcgis",
        "layerName": params.get("layer_name"),
        "sublayerName": params.get("sublayer_name"),
        "featureServiceAddress": resource_params.get("feature_service_address"),
        "tokenSet": token_set,
    }


def get_module_data(
    pipeline_name: str, module_name: str, module_index: int | None = None
) -> dict[str, Any]:

    validate_module_index(module_index)

    match module_name:
        case "http_get":
            return get_http_get_data(pipeline_name, module_index=module_index)
        case "json_mapper":
            return get_json_mapper_data(pipeline_name, module_index=module_index)
        case "write_to_csv":
            return get_write_to_csv_data(pipeline_name, module_index=module_index)
        case "transform_to_arcgis_format":
            return get_transform_to_arcgis_format_data(pipeline_name, module_index=module_index)
        case "send_to_arcgis":
            return get_send_to_arcgis_data(pipeline_name, module_index=module_index)
        case _:
            raise ValueError(f"Unsupported module_name: {module_name}")
