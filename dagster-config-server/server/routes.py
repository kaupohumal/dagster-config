from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.job_config import update_job_config

api = Blueprint("api", __name__)


@api.post("/config")
def update_config():
    payload = request.get_json(silent=True) or {}

    try:
        resp = update_job_config(payload)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500

    return jsonify(resp), 200
