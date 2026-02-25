import os
import yaml

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

YAML_FILE = os.path.join(os.path.dirname(__file__), "/home/kaupo/kool/thesis/dagster/dagster-user-code/jobs/bus_validations.yaml")


def find_asset_by_module(config: dict, module_name: str) -> dict | None:
    for job in config.get("jobs", []) or []:
        for asset in job.get("assets", []) or []:
            if asset.get("module") == module_name:
                return asset
    return None


def mappings_list_to_dict(mappings_list: object) -> dict:
    """Convert request payload list of {source,target} into YAML mappings dict.

    Request example:
      [{'source': 'coord.lon', 'target': 'lon'}, ...]

    YAML expects:
      mappings:
        lon: coord.lon
    """
    if mappings_list is None:
        raise ValueError("Missing 'mappings'.")
    if not isinstance(mappings_list, list):
        raise ValueError("'mappings' must be a list of {source,target} objects.")

    out: dict = {}
    for i, item in enumerate(mappings_list):
        if not isinstance(item, dict):
            raise ValueError(f"mappings[{i}] must be an object.")
        source = item.get("source")
        target = item.get("target")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"mappings[{i}].source must be a non-empty string.")
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"mappings[{i}].target must be a non-empty string.")
        if target in out:
            raise ValueError(f"Duplicate target '{target}' in mappings.")
        # Preserve request order (Python 3.7+ dict insertion order)
        out[target] = source

    return out


def set_units(config: dict, new_units: str) -> int:
    updated = 0
    for job in config.get('jobs', []):
        for asset in job.get('assets', []):
            inner = asset.get('params', {}).get('params')
            if isinstance(inner, dict) and 'units' in inner:
                inner['units'] = new_units
                updated += 1
    return updated


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML file not found: {path}")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_config(path: str, data: dict) -> None:
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


@app.post("/units")
def update_units():
    payload = request.get_json(silent=True) or {}
    units = (
        payload.get("units")
        or request.form.get("units")
        or request.args.get("units")
    )

    if not units:
        return jsonify({
            "ok": False,
            "error": "Missing 'units'. Provide via JSON body, form field, or query parameter."
        }), 400

    allowed = {"standard", "metric", "imperial"}
    if units not in allowed:
        return jsonify({
            "ok": False,
            "error": f"Invalid units '{units}'. Allowed: {sorted(allowed)}"
        }), 400

    try:
        data = load_config(YAML_FILE)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read YAML: {e}"}), 500

    try:
        updated = set_units(data, units)
        save_config(YAML_FILE, data)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500

    return jsonify({
        "ok": True,
        "units": units,
        "updated": updated,
        "file": os.path.basename(YAML_FILE),
    }), 200


@app.post("/config")
def update_config():
    payload = request.get_json(silent=True) or {}

    try:
        data = load_config(YAML_FILE)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read YAML: {e}"}), 500

    http_asset = find_asset_by_module(data, "http_get")
    if not http_asset:
        return jsonify({"ok": False, "error": "No asset with module 'http_get' found."}), 404

    if "timeseriesApiEndpoint" in payload:
        http_asset.setdefault("params", {})["endpoint"] = payload.get("timeseriesApiEndpoint")

    json_asset = find_asset_by_module(data, "json_mapper")
    if not json_asset:
        return jsonify({"ok": False, "error": "No asset with module 'json_mapper' found."}), 404

    if "mappings" in payload:
        try:
            new_mappings = mappings_list_to_dict(payload.get("mappings"))
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

        json_asset.setdefault("params", {})["mappings"] = new_mappings

    csv_asset = find_asset_by_module(data, "write_to_csv")
    if not csv_asset:
        return jsonify({"ok": False, "error": "No asset with module 'csv_asset' found."}), 404

    if "fileName" in payload:
        csv_asset.setdefault("params", {})["file_name"] = payload.get("fileName")

    try:
        save_config(YAML_FILE, data)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500

    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    app.run(debug=True)