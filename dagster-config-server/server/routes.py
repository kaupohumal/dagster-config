from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.job_config import update_job_config
from .services.modules import list_module_names_for_pipeline
from .services.pipelines import list_pipeline_names

api = Blueprint("api", __name__)


@api.get("/pipelines")
def get_pipeline_names():
    try:
        names = list_pipeline_names()
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except NotADirectoryError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to list pipelines: {e}"}), 500

    return jsonify(names), 200


@api.get("/pipelines/<pipeline_name>/modules")
def get_pipeline_modules(pipeline_name: str):
    try:
        modules = list_module_names_for_pipeline(pipeline_name)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to list modules: {e}"}), 500

    return jsonify(modules), 200


# TODO: specify job
@api.patch("/assets/<module_name>")
def update_config(module_name: str):
    payload = request.get_json(silent=True) or {}

    try:
        resp = update_job_config(module_name, payload)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500

    return jsonify(resp), 200
