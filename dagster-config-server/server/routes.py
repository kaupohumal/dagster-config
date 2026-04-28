from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.dagster_graphql import DagsterGraphQLError, get_run_status, trigger_pipeline_run
from .services.job_config import update_module_config
from .services.modules import (
    add_module_to_pipeline,
    create_pipeline_from_modules,
    list_module_catalog,
    list_module_entries_for_pipeline,
    list_module_names_for_pipeline,
    remove_module_from_pipeline,
    swap_module_for_pipeline_asset,
)
from .services.pipelines import (
    copy_pipeline,
    get_pipeline_schedule,
    list_pipeline_names,
    set_pipeline_schedule,
    delete_pipeline,
)
from .services.modules import get_module_data as get_module_data_service
from .services.run_config import apply_arcgis_resource_config, apply_minio_resource_config

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


@api.get("/module-catalog")
def get_module_catalog():
    return jsonify(list_module_catalog()), 200


@api.get("/pipelines/<pipeline_name>/module-entries")
def get_pipeline_module_entries(pipeline_name: str):
    try:
        entries = list_module_entries_for_pipeline(pipeline_name)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to list module entries: {e}"}), 500

    return jsonify(entries), 200


@api.get("/pipelines/<pipeline_name>/schedule")
def get_schedule_for_pipeline(pipeline_name: str):
    try:
        data = get_pipeline_schedule(pipeline_name)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to get schedule: {e}"}), 500

    return jsonify(data), 200


@api.patch("/pipelines/<pipeline_name>/schedule")
def update_schedule_for_pipeline(pipeline_name: str):
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or "cron" not in payload:
        return jsonify({"ok": False, "error": "payload must include 'cron' (string or null)."}), 400

    try:
        resp = set_pipeline_schedule(
            pipeline_name=pipeline_name,
            cron=payload.get("cron"),
        )
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to update schedule: {e}"}), 500

    return jsonify(resp), 200


@api.post("/pipelines")
def create_pipeline():
    payload = request.get_json(silent=True) or {}

    pipeline_name = payload.get("pipelineName") if isinstance(payload, dict) else None
    modules = payload.get("modules") if isinstance(payload, dict) else None
    job_name = payload.get("jobName") if isinstance(payload, dict) else None

    try:
        result = create_pipeline_from_modules(
            pipeline_name=pipeline_name,
            module_specs=modules,
            job_name=job_name,
        )
    except FileExistsError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except EnvironmentError as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to create pipeline: {e}"}), 500

    return jsonify(result), 201


@api.post("/pipelines/<pipeline_name>/copy")
def copy_pipeline_route(pipeline_name: str):
    payload = request.get_json(silent=True) or {}

    target_pipeline_name = payload.get("targetPipelineName") if isinstance(payload, dict) else None

    if not isinstance(target_pipeline_name, str) or not target_pipeline_name.strip():
        return jsonify({"ok": False, "error": "payload must include 'targetPipelineName' (string)."}), 400

    try:
        result = copy_pipeline(
            source_pipeline_name=pipeline_name,
            target_pipeline_name=target_pipeline_name,
        )
    except FileExistsError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to copy pipeline: {e}"}), 500

    return jsonify(result), 201



@api.delete("/pipelines/<pipeline_name>")
def delete_pipeline_route(pipeline_name: str):
    try:
        result = delete_pipeline(pipeline_name)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to delete pipeline: {e}"}), 500

    return jsonify(result), 200


@api.patch("/pipelines/<pipeline_name>/assets/<int:asset_index>/module")
def swap_pipeline_asset_module(pipeline_name: str, asset_index: int):
    payload = request.get_json(silent=True) or {}

    target_module = payload.get("targetModule") if isinstance(payload, dict) else None
    preserve_compatible_params = bool(payload.get("preserveCompatibleParams", True))
    dry_run = bool(payload.get("dryRun", False))

    try:
        result = swap_module_for_pipeline_asset(
            pipeline_name=pipeline_name,
            asset_index=asset_index,
            target_module_name=target_module,
            preserve_compatible_params=preserve_compatible_params,
            dry_run=dry_run,
        )
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to swap module: {e}"}), 500

    return jsonify(result), 200


@api.post("/pipelines/<pipeline_name>/assets")
def add_pipeline_asset_module(pipeline_name: str):
    payload = request.get_json(silent=True) or {}

    target_module = payload.get("targetModule") if isinstance(payload, dict) else None
    insert_index = payload.get("insertIndex") if isinstance(payload, dict) else None
    asset_name = payload.get("assetName") if isinstance(payload, dict) else None
    group = payload.get("group") if isinstance(payload, dict) else None
    params = payload.get("params") if isinstance(payload, dict) else None

    try:
        result = add_module_to_pipeline(
            pipeline_name=pipeline_name,
            target_module_name=target_module,
            insert_index=insert_index,
            asset_name=asset_name,
            group=group,
            params=params,
        )
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to add module: {e}"}), 500

    return jsonify(result), 201


@api.delete("/pipelines/<pipeline_name>/assets/<int:asset_index>")
def remove_pipeline_asset_module(pipeline_name: str, asset_index: int):
    try:
        result = remove_module_from_pipeline(
            pipeline_name=pipeline_name,
            asset_index=asset_index,
        )
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except LookupError as e:
        return jsonify({"ok": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to remove module: {e}"}), 500

    return jsonify(result), 200


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


@api.get("/pipelines/<pipeline_name>/modules/<module_name>/<int:module_index>")
def get_module_data_by_index(pipeline_name: str, module_name: str, module_index: int):
    try:
        data = get_module_data_service(pipeline_name, module_name, module_index=module_index)
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


@api.patch("/pipelines/<pipeline_name>/modules/<module_name>/<int:module_index>")
def update_module_data_by_index(pipeline_name: str, module_name: str, module_index: int):
    payload = request.get_json(silent=True) or {}

    try:
        resp = update_module_config(
            pipeline_name,
            module_name,
            payload,
            module_index=module_index,
        )
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
        run_config_data = apply_minio_resource_config(
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


