from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys
import importlib
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

modules_service = importlib.import_module("server.services.modules")
pipelines_service = importlib.import_module("server.services.pipelines")
yaml_loader = importlib.import_module("server.services.yaml_loader")
job_config_service = importlib.import_module("server.services.job_config")

create_pipeline_from_modules = modules_service.create_pipeline_from_modules
list_module_entries_for_pipeline = modules_service.list_module_entries_for_pipeline
swap_module_for_pipeline_asset = modules_service.swap_module_for_pipeline_asset
add_module_to_pipeline = modules_service.add_module_to_pipeline
remove_module_from_pipeline = modules_service.remove_module_from_pipeline
get_module_data = modules_service.get_module_data
get_pipeline_schedule = pipelines_service.get_pipeline_schedule
set_pipeline_schedule = pipelines_service.set_pipeline_schedule
update_module_config = job_config_service.update_module_config
load_config = yaml_loader.load_config


class PipelineBuilderTests(unittest.TestCase):
    def test_create_pipeline_from_modules_creates_linear_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_pipeline_from_modules(
                pipeline_name="new_pipeline",
                module_specs=[
                    "http_get",
                    {"module": "json_mapper", "params": {"mappings": {"a": "b"}}},
                    "send_to_arcgis",
                ],
                pipelines_dir=tmpdir,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["moduleCount"], 3)

            yaml_path = Path(tmpdir) / "new_pipeline.yaml"
            self.assertTrue(yaml_path.exists())

            config = load_config(str(yaml_path))
            assets = config["jobs"][0]["assets"]
            self.assertEqual(assets[1]["ins"], assets[0]["asset"])
            self.assertEqual(assets[2]["ins"], assets[1]["asset"])
            self.assertEqual(assets[2]["module"], "send_to_arcgis")
            self.assertTrue(isinstance(config.get("resources"), list) and len(config["resources"]) == 1)

    def test_create_pipeline_rejects_invalid_name_characters(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                create_pipeline_from_modules(
                    pipeline_name="invalid-name",
                    module_specs=["http_get"],
                    pipelines_dir=tmpdir,
                )

    def test_create_pipeline_rejects_python_keyword_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                create_pipeline_from_modules(
                    pipeline_name="for",
                    module_specs=["http_get"],
                    pipelines_dir=tmpdir,
                )

    def test_create_pipeline_allows_dagster_alphanumeric_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_pipeline_from_modules(
                pipeline_name="2fast_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["pipeline"], "2fast_pipeline")

    def test_list_module_entries_for_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="entries_pipeline",
                module_specs=["http_get", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            entries = list_module_entries_for_pipeline("entries_pipeline", pipelines_dir=tmpdir)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["name"], "http_get")
            self.assertEqual(entries[1]["name"], "write_to_csv")
            self.assertEqual(entries[1]["index"], 1)

    def test_swap_module_dry_run_does_not_persist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="dry_run_pipeline",
                module_specs=["http_get", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            result = swap_module_for_pipeline_asset(
                pipeline_name="dry_run_pipeline",
                asset_index=1,
                target_module_name="send_to_arcgis",
                pipelines_dir=tmpdir,
                dry_run=True,
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["changed"])
            self.assertTrue(result["dryRun"])

            config = load_config(str(Path(tmpdir) / "dry_run_pipeline.yaml"))
            assets = config["jobs"][0]["assets"]
            self.assertEqual(assets[1]["module"], "write_to_csv")
            resources = config.get("resources")
            self.assertTrue(isinstance(resources, list) and len(resources) == 1)
            self.assertEqual(resources[0].get("resource"), "MinIO")

    def test_swap_module_persists_and_adds_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="swap_pipeline",
                module_specs=["http_get", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            result = swap_module_for_pipeline_asset(
                pipeline_name="swap_pipeline",
                asset_index=1,
                target_module_name="send_to_arcgis",
                pipelines_dir=tmpdir,
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["module"], "send_to_arcgis")
            self.assertIn("ArcGIS", result["diagnostics"]["addedResources"])

            config = load_config(str(Path(tmpdir) / "swap_pipeline.yaml"))
            assets = config["jobs"][0]["assets"]
            self.assertEqual(assets[1]["module"], "send_to_arcgis")
            self.assertEqual(assets[1]["params"]["layer_name"], "")
            resources = config.get("resources")
            self.assertTrue(isinstance(resources, list) and len(resources) == 2)
            arcgis_resource = next((resource for resource in resources if resource.get("resource") == "ArcGIS"), None)
            self.assertIsNotNone(arcgis_resource)
            self.assertEqual(arcgis_resource["params"]["token"], "")

    def test_send_to_arcgis_token_is_write_only_in_module_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir

            create_pipeline_from_modules(
                pipeline_name="arcgis_token_pipeline",
                module_specs=["send_to_arcgis"],
                pipelines_dir=tmpdir,
            )

            try:
                initial_module_data = get_module_data(
                    "arcgis_token_pipeline", "send_to_arcgis", module_index=0
                )
                self.assertFalse(initial_module_data["tokenSet"])
                self.assertNotIn("token", initial_module_data)

                update_module_config(
                    pipeline_name="arcgis_token_pipeline",
                    module_name="send_to_arcgis",
                    payload={"arcgisToken": "super-secret-token"},
                    module_index=0,
                )

                updated_module_data = get_module_data(
                    "arcgis_token_pipeline", "send_to_arcgis", module_index=0
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            self.assertTrue(updated_module_data["tokenSet"])
            self.assertNotIn("token", updated_module_data)

            config = load_config(str(Path(tmpdir) / "arcgis_token_pipeline.yaml"))
            resource = config["resources"][0]
            self.assertEqual(resource["params"]["token"], "super-secret-token")

    def test_create_pipeline_with_write_to_csv_adds_minio_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="csv_pipeline",
                module_specs=["write_to_csv"],
                pipelines_dir=tmpdir,
            )

            config = load_config(str(Path(tmpdir) / "csv_pipeline.yaml"))
            asset = config["jobs"][0]["assets"][0]
            resources = config.get("resources")
            self.assertEqual(asset["params"]["minio"]["bucket"], "dagster-integration")
            self.assertTrue(isinstance(resources, list) and len(resources) == 1)
            self.assertEqual(resources[0]["resource"], "MinIO")
            self.assertEqual(resources[0]["name"], "minio")

    def test_write_to_csv_secret_key_is_write_only_in_module_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir

            create_pipeline_from_modules(
                pipeline_name="csv_secret_pipeline",
                module_specs=["write_to_csv"],
                pipelines_dir=tmpdir,
            )

            try:
                initial_module_data = get_module_data(
                    "csv_secret_pipeline", "write_to_csv", module_index=0
                )
                self.assertFalse(initial_module_data["minioSecretKeySet"])
                self.assertNotIn("minioSecretKey", initial_module_data)
                self.assertEqual(initial_module_data["minioBucket"], "dagster-integration")

                update_module_config(
                    pipeline_name="csv_secret_pipeline",
                    module_name="write_to_csv",
                    payload={
                        "minioBucket": "integration-results",
                        "minioHost": "https://minio.local",
                        "minioAccessKey": "MINIO_ACCESS_KEY",
                        "minioSecretKey": "MINIO_SECRET_KEY",
                    },
                    module_index=0,
                )

                updated_module_data = get_module_data(
                    "csv_secret_pipeline", "write_to_csv", module_index=0
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            self.assertTrue(updated_module_data["minioSecretKeySet"])
            self.assertNotIn("minioSecretKey", updated_module_data)
            self.assertEqual(updated_module_data["minioBucket"], "integration-results")
            self.assertEqual(updated_module_data["minioHost"], "https://minio.local")
            self.assertEqual(updated_module_data["minioAccessKey"], "MINIO_ACCESS_KEY")

            config = load_config(str(Path(tmpdir) / "csv_secret_pipeline.yaml"))
            asset = config["jobs"][0]["assets"][0]
            resource = config["resources"][0]
            self.assertEqual(asset["params"]["minio"]["bucket"], "integration-results")
            self.assertEqual(resource["params"]["secret_key"], "MINIO_SECRET_KEY")

    def test_indexed_module_read_for_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="duplicate_http",
                module_specs=[
                    {"module": "http_get", "params": {"endpoint": "https://one.example"}},
                    {"module": "http_get", "params": {"endpoint": "https://two.example"}},
                ],
                pipelines_dir=tmpdir,
            )

            try:
                first = get_module_data("duplicate_http", "http_get", module_index=0)
                second = get_module_data("duplicate_http", "http_get", module_index=1)
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            self.assertEqual(first["endpoint"], "https://one.example")
            self.assertEqual(second["endpoint"], "https://two.example")

    def test_http_get_auth_is_write_only_in_module_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="http_auth_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            try:
                update_module_config(
                    pipeline_name="http_auth_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "basic_auth": {
                                "username": "service-user",
                                "password": "service-password",
                            }
                        }
                    },
                    module_index=0,
                )

                module_data = get_module_data("http_auth_pipeline", "http_get", module_index=0)

                update_module_config(
                    pipeline_name="http_auth_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "basic_auth": {
                                "username": "updated-user",
                            }
                        }
                    },
                    module_index=0,
                )

                update_module_config(
                    pipeline_name="http_auth_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "api_key": {
                                "key": "{{ env.TIMESERIES_API_KEY }}",
                                "key_name": "api_key",
                            }
                        }
                    },
                    module_index=0,
                )

                api_key_module_data = get_module_data(
                    "http_auth_pipeline", "http_get", module_index=0
                )

                update_module_config(
                    pipeline_name="http_auth_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "bearer_token": {
                                "token": "token-value",
                            }
                        }
                    },
                    module_index=0,
                )

                bearer_module_data = get_module_data(
                    "http_auth_pipeline", "http_get", module_index=0
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            self.assertEqual(
                module_data["auth"],
                {"basic_auth": {"username": "service-user", "passwordSet": True}},
            )
            self.assertNotIn("password", module_data["auth"]["basic_auth"])
            self.assertEqual(
                api_key_module_data["auth"],
                {"api_key": {"key_name": "api_key", "keySet": True}},
            )
            self.assertNotIn("key", api_key_module_data["auth"]["api_key"])
            self.assertEqual(
                bearer_module_data["auth"],
                {"bearer_token": {"tokenSet": True}},
            )
            self.assertNotIn("token", bearer_module_data["auth"]["bearer_token"])

            config = load_config(str(Path(tmpdir) / "http_auth_pipeline.yaml"))
            auth = config["jobs"][0]["assets"][0]["params"]["auth"]
            self.assertEqual(
                auth,
                {
                    "bearer_token": {
                        "token": "token-value",
                    }
                },
            )

    def test_http_get_auth_preserves_secret_on_partial_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="http_auth_partial_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            try:
                update_module_config(
                    pipeline_name="http_auth_partial_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "api_key": {
                                "key_name": "api_key",
                                "key": "SECRET",
                            }
                        }
                    },
                    module_index=0,
                )

                update_module_config(
                    pipeline_name="http_auth_partial_pipeline",
                    module_name="http_get",
                    payload={
                        "auth": {
                            "api_key": {
                                "key_name": "x-api-key",
                            }
                        }
                    },
                    module_index=0,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "http_auth_partial_pipeline.yaml"))
            auth = config["jobs"][0]["assets"][0]["params"]["auth"]
            self.assertEqual(auth["api_key"]["key"], "SECRET")
            self.assertEqual(auth["api_key"]["key_name"], "x-api-key")

    def test_http_get_auth_rejects_multiple_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="http_auth_invalid_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            try:
                with self.assertRaises(ValueError):
                    update_module_config(
                        pipeline_name="http_auth_invalid_pipeline",
                        module_name="http_get",
                        payload={
                            "auth": {
                                "api_key": {
                                    "key": "A",
                                    "key_name": "api_key",
                                },
                                "bearer_token": {
                                    "token": "B",
                                },
                            }
                        },
                        module_index=0,
                    )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

    def test_indexed_module_update_for_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="duplicate_csv",
                module_specs=[
                    {"module": "write_to_csv", "params": {"file_name": "first.csv"}},
                    {"module": "write_to_csv", "params": {"file_name": "second.csv"}},
                ],
                pipelines_dir=tmpdir,
            )

            try:
                update_module_config(
                    pipeline_name="duplicate_csv",
                    module_name="write_to_csv",
                    payload={"fileName": "updated-second.csv"},
                    module_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "duplicate_csv.yaml"))
            assets = config["jobs"][0]["assets"]

            self.assertEqual(assets[0]["params"]["file_name"], "first.csv")
            self.assertEqual(assets[1]["params"]["file_name"], "updated-second.csv")

    def test_add_module_rewires_linear_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="add_pipeline",
                module_specs=["http_get", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            try:
                add_module_to_pipeline(
                    pipeline_name="add_pipeline",
                    target_module_name="json_mapper",
                    insert_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "add_pipeline.yaml"))
            assets = config["jobs"][0]["assets"]
            self.assertEqual([asset["module"] for asset in assets], ["http_get", "json_mapper", "write_to_csv"])
            self.assertEqual(assets[1]["ins"], assets[0]["asset"])
            self.assertEqual(assets[2]["ins"], assets[1]["asset"])

    def test_remove_module_rewires_linear_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="remove_pipeline",
                module_specs=["http_get", "json_mapper", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            try:
                remove_module_from_pipeline(
                    pipeline_name="remove_pipeline",
                    asset_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "remove_pipeline.yaml"))
            assets = config["jobs"][0]["assets"]
            self.assertEqual([asset["module"] for asset in assets], ["http_get", "write_to_csv"])
            self.assertEqual(assets[1]["ins"], assets[0]["asset"])

    def test_remove_write_to_csv_removes_unused_minio_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="remove_minio_pipeline",
                module_specs=["http_get", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            try:
                result = remove_module_from_pipeline(
                    pipeline_name="remove_minio_pipeline",
                    asset_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "remove_minio_pipeline.yaml"))
            self.assertEqual(result.get("removedResources"), ["MinIO"])
            self.assertEqual([asset["module"] for asset in config["jobs"][0]["assets"]], ["http_get"])
            self.assertEqual(config.get("resources"), [])

    def test_remove_send_to_arcgis_removes_unused_arcgis_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="remove_arcgis_pipeline",
                module_specs=["http_get", "send_to_arcgis"],
                pipelines_dir=tmpdir,
            )

            try:
                result = remove_module_from_pipeline(
                    pipeline_name="remove_arcgis_pipeline",
                    asset_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "remove_arcgis_pipeline.yaml"))
            self.assertEqual(result.get("removedResources"), ["ArcGIS"])
            self.assertEqual([asset["module"] for asset in config["jobs"][0]["assets"]], ["http_get"])
            self.assertEqual(config.get("resources"), [])

    def test_remove_module_keeps_resource_when_still_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = os.environ.get("JOBS_DIR")
            os.environ["JOBS_DIR"] = tmpdir
            create_pipeline_from_modules(
                pipeline_name="keep_resource_pipeline",
                module_specs=["write_to_csv", "write_to_csv"],
                pipelines_dir=tmpdir,
            )

            try:
                result = remove_module_from_pipeline(
                    pipeline_name="keep_resource_pipeline",
                    asset_index=1,
                )
            finally:
                if previous_jobs_dir is None:
                    del os.environ["JOBS_DIR"]
                else:
                    os.environ["JOBS_DIR"] = previous_jobs_dir

            config = load_config(str(Path(tmpdir) / "keep_resource_pipeline.yaml"))
            self.assertEqual(result.get("removedResources"), [])
            resources = config.get("resources")
            self.assertTrue(isinstance(resources, list) and len(resources) == 1)
            self.assertEqual(resources[0].get("resource"), "MinIO")

    def test_schedule_can_be_added_and_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="scheduled_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            initial = get_pipeline_schedule("scheduled_pipeline", pipelines_dir=tmpdir)
            self.assertFalse(initial["hasSchedule"])
            self.assertIsNone(initial["cron"])

            added = set_pipeline_schedule(
                pipeline_name="scheduled_pipeline",
                cron="*/5 * * * *",
                pipelines_dir=tmpdir,
            )
            self.assertTrue(added["hasSchedule"])
            self.assertEqual(added["cron"], "*/5 * * * *")

            removed = set_pipeline_schedule(
                pipeline_name="scheduled_pipeline",
                cron=None,
                pipelines_dir=tmpdir,
            )
            self.assertFalse(removed["hasSchedule"])
            self.assertIsNone(removed["cron"])

            config = load_config(str(Path(tmpdir) / "scheduled_pipeline.yaml"))
            self.assertNotIn("schedule", config["jobs"][0])

    def test_schedule_rejects_invalid_cron(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            create_pipeline_from_modules(
                pipeline_name="bad_cron_pipeline",
                module_specs=["http_get"],
                pipelines_dir=tmpdir,
            )

            with self.assertRaises(ValueError):
                set_pipeline_schedule(
                    pipeline_name="bad_cron_pipeline",
                    cron="every five minutes",
                    pipelines_dir=tmpdir,
                )


if __name__ == "__main__":
    unittest.main()






