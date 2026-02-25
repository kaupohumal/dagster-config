import os
import yaml

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# YAML_FILE = os.path.join(os.path.dirname(__file__), "bus_validations.yaml")
YAML_FILE = os.path.join(os.path.dirname(__file__), "/home/kaupo/kool/thesis/dagster/dagster-user-code/jobs/bus_validations.yaml")

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
    print(payload)

    try:
        data = load_config(YAML_FILE)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to read YAML: {e}"}), 500

    http_asset = next(
        asset
        for job in data.get("jobs", [])
        for asset in job.get("assets", [])
        if asset.get("module") == "http_get"
    )

    current_endpoint = http_asset["params"]["endpoint"]
    print("current endpoint:", current_endpoint)

    http_asset["params"]["endpoint"] = payload.get("sourceApiUrl")

    try:
        save_config(YAML_FILE, data)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500


    return payload
