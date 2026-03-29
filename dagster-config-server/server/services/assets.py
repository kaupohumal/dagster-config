from __future__ import annotations

from typing import Any


def find_asset_by_module(config: dict[str, Any], module_name: str) -> dict[str, Any] | None:

    for job in config.get("jobs", []) or []:
        for asset in job.get("assets", []) or []:
            if asset.get("module") == module_name:
                return asset
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


