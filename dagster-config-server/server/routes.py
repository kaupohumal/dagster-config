from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.dagster_graphql import DagsterGraphQLError, get_run_status, trigger_pipeline_run
from .services.job_config import update_module_config
from .services.modules import list_module_names_for_pipeline
from .services.pipelines import list_pipeline_names
from .services.modules import get_module_data as get_module_data_service
from .services.run_config import apply_arcgis_resource_config

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


@api.get("/pipelines/<pipeline_name>/modules/<module_name>")
def get_module_data(pipeline_name: str, module_name: str):
    try:
        data = get_module_data_service(pipeline_name, module_name)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to get module data: {e}"}), 500

    return jsonify(data), 200


@api.patch("/pipelines/<pipeline_name>/modules/<module_name>")
def update_module_data(pipeline_name: str, module_name: str):
    payload = request.get_json(silent=True) or {}

    try:
        resp = update_module_config(pipeline_name, module_name, payload)
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update YAML: {e}"}), 500

    return jsonify(resp), 200


@api.post("/pipelines/<pipeline_name>/run")
def run_pipeline(pipeline_name: str):
    payload = request.get_json(silent=True) or {}

    run_config_data = payload.get("runConfigData") if isinstance(payload, dict) else None
    if run_config_data is not None and not isinstance(run_config_data, dict):
        return jsonify({"ok": False, "error": "runConfigData must be an object."}), 400

    try:
        run_config_data = apply_arcgis_resource_config(
            pipeline_name=pipeline_name,
            run_config_data=run_config_data,
        )
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    raw_tags = payload.get("tags") if isinstance(payload, dict) else None
    if raw_tags is not None and not isinstance(raw_tags, dict):
        return jsonify({"ok": False, "error": "tags must be an object."}), 400
    tags = {str(key): str(value) for key, value in (raw_tags or {}).items()}

    target_name = payload.get("jobName") if isinstance(payload, dict) else None
    if target_name is not None and not isinstance(target_name, str):
        return jsonify({"ok": False, "error": "jobName must be a string."}), 400

    try:
        result = trigger_pipeline_run(
            pipeline_name=target_name or pipeline_name,
            run_config_data=run_config_data,
            tags=tags,
        )
    except EnvironmentError as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    except DagsterGraphQLError as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to launch pipeline run: {e}"}), 500

    status_code = 200 if result.ok else 400
    return jsonify(result.to_dict()), status_code


@api.get("/pipelines/<pipeline_name>/runs/<run_id>/status")
def get_pipeline_run_status(pipeline_name: str, run_id: str):
    _ = pipeline_name

    try:
        result = get_run_status(run_id)
    except EnvironmentError as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    except DagsterGraphQLError as e:
        return jsonify({"ok": False, "error": str(e)}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to fetch run status: {e}"}), 500

    if result.ok:
        return jsonify(result.to_dict()), 200
    if result.error_type == "RunNotFoundError":
        return jsonify(result.to_dict()), 404
    return jsonify(result.to_dict()), 502


