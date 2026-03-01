from __future__ import annotations

from typing import Any

from .assets import find_asset_by_module, mappings_list_to_dict
from .yaml_loader import load_config, save_config


def update_job_config(module_name: str, payload: dict[str, Any]) -> dict[str, Any]:

    yaml_file = "/home/kaupo/kool/thesis/dagster/dagster-user-code/jobs/bus_validations.yaml"

    data = load_config(yaml_file)

    asset = find_asset_by_module(data, module_name)
    if not asset:
        raise LookupError("No asset with module " + module_name + " found.")

    # TODO: kas peaks loopima üle payloadi võtmete või hardcodema sisse iga mooduli puhul, mida on lubatud muuta?
    # hardcodemine vist ei ole vajalik, sest kui võtit yaml failist ei leita, siis järelikult pole lubatud

# TODO järgmisena: see loogika edasi, FE-s mooduli confi valik, kus hoida yaml faile?

    http_asset = find_asset_by_module(data, "http_get")
    if not http_asset:
        raise LookupError("No asset with module 'http_get' found.")

    if "timeseriesApiEndpoint" in payload:
        http_asset.setdefault("params", {})["endpoint"] = payload.get("timeseriesApiEndpoint")

    json_asset = find_asset_by_module(data, "json_mapper")
    if not json_asset:
        raise LookupError("No asset with module 'json_mapper' found.")

    if "mappings" in payload:
        new_mappings = mappings_list_to_dict(payload.get("mappings"))
        json_asset.setdefault("params", {})["mappings"] = new_mappings

    csv_asset = find_asset_by_module(data, "write_to_csv")
    if not csv_asset:
        raise LookupError("No asset with module 'write_to_csv' found.")

    if "fileName" in payload:
        csv_asset.setdefault("params", {})["file_name"] = payload.get("fileName")

    save_config(yaml_file, data)

    return {"ok": True}

#TODO: teha assetipõhine loogika
#assetid: http_get, json_mapper, csv, timestamp, arcgis transform, arcgis