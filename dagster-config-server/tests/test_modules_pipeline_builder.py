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
yaml_loader = importlib.import_module("server.services.yaml_loader")
job_config_service = importlib.import_module("server.services.job_config")

create_pipeline_from_modules = modules_service.create_pipeline_from_modules
list_module_entries_for_pipeline = modules_service.list_module_entries_for_pipeline
swap_module_for_pipeline_asset = modules_service.swap_module_for_pipeline_asset
add_module_to_pipeline = modules_service.add_module_to_pipeline
remove_module_from_pipeline = modules_service.remove_module_from_pipeline
get_module_data = modules_service.get_module_data
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
            self.assertFalse(config.get("resources"))

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
            self.assertTrue(isinstance(config.get("resources"), list) and len(config["resources"]) == 1)

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


if __name__ == "__main__":
    unittest.main()






