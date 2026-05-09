from __future__ import annotations

from typing import Any


def find_asset_by_module(config: dict[str, Any], module_name: str) -> dict[str, Any] | None:

    for job in config.get("jobs", []) or []:
        for asset in job.get("assets", []) or []:
            if asset.get("module") == module_name:
                return asset
    return None


def find_asset_by_module_entry_index(
    config: dict[str, Any],
    module_entry_index: int,
) -> dict[str, Any] | None:
    if not isinstance(module_entry_index, int) or module_entry_index < 0:
        return None

    current_index = 0
    for job in config.get("jobs", []) or []:
        if not isinstance(job, dict):
            continue
        for asset in job.get("assets", []) or []:
            if not isinstance(asset, dict):
                continue
            module_name = asset.get("module")
            if not isinstance(module_name, str) or not module_name.strip():
                continue
            if current_index == module_entry_index:
                return asset
            current_index += 1
    return None


def find_asset_by_module_and_entry_index(
    config: dict[str, Any],
    module_name: str,
    module_entry_index: int,
) -> dict[str, Any] | None:
    asset = find_asset_by_module_entry_index(config, module_entry_index)
    if not asset:
        return None

    resolved_module = asset.get("module")
    if not isinstance(resolved_module, str) or resolved_module.strip() != module_name:
        raise LookupError(
            f"Asset at index {module_entry_index} is not module '{module_name}'."
        )
    return asset


def validate_module_index(module_index: int | None) -> int | None:
    if module_index is None:
        return None
    if not isinstance(module_index, int) or module_index < 0:
        raise ValueError("module_index must be a non-negative integer")
    return module_index


def find_module_asset_or_error(
    config: dict[str, Any],
    module_name: str,
    module_index: int | None,
) -> dict[str, Any]:
    validate_module_index(module_index)

    if module_index is None:
        asset = find_asset_by_module(config, module_name)
    else:
        asset = find_asset_by_module_and_entry_index(config, module_name, module_index)

    if not asset:
        if module_index is None:
            raise LookupError(f"No asset with module '{module_name}' found.")
        raise LookupError(f"No asset with module '{module_name}' found at index {module_index}.")
    return asset


def find_resource_by_type(config: dict[str, Any], resource_type: str) -> dict[str, Any] | None:

    for resource in config.get("resources", []) or []:
        if isinstance(resource, dict) and resource.get("resource") == resource_type:
            return resource
    return None


def pair_list_to_dict(
    pair_list: object,
    *,
    payload_name: str,
    key_field: str,
    value_field: str,
) -> dict[str, str]:

    if pair_list is None:
        raise ValueError(f"Missing '{payload_name}'.")
    if not isinstance(pair_list, list):
        raise ValueError(
            f"'{payload_name}' must be a list of {{{key_field},{value_field}}} objects."
        )

    out: dict[str, str] = {}
    for i, item in enumerate(pair_list):
        if not isinstance(item, dict):
            raise ValueError(f"{payload_name}[{i}] must be an object.")

        key = item.get(key_field)
        value = item.get(value_field)

        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                f"{payload_name}[{i}].{key_field} must be a non-empty string."
            )
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{payload_name}[{i}].{value_field} must be a non-empty string."
            )
        if key in out:
            raise ValueError(f"Duplicate {key_field} '{key}' in {payload_name}.")

        out[key] = value

    return out


def dict_to_pair_list(
    raw: object,
    *,
    key_field: str,
    value_field: str,
) -> list[dict[str, str]]:

    if not isinstance(raw, dict):
        return []

    pair_list: list[dict[str, str]] = []
    for key, value in raw.items():
        if key is None or value is None:
            continue
        pair_list.append({key_field: str(key), value_field: str(value)})

    pair_list.sort(key=lambda x: (x.get(key_field, ""), x.get(value_field, "")))
    return pair_list


def key_value_list_to_dict(pair_list: object, payload_name: str = "params") -> dict[str, str]:
    return pair_list_to_dict(
        pair_list,
        payload_name=payload_name,
        key_field="key",
        value_field="value",
    )


def mappings_list_to_dict(mappings_list: object) -> dict[str, str]:
    return pair_list_to_dict(
        mappings_list,
        payload_name="mappings",
        key_field="key",
        value_field="value",
    )


