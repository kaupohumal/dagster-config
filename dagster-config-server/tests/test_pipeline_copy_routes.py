from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

create_app = importlib.import_module("server.create_app").create_app
modules_service = importlib.import_module("server.services.modules")
pipelines_service = importlib.import_module("server.services.pipelines")
yaml_loader = importlib.import_module("server.services.yaml_loader")

create_pipeline_from_modules = modules_service.create_pipeline_from_modules
set_pipeline_schedule = pipelines_service.set_pipeline_schedule
load_config = yaml_loader.load_config


class PipelineCopyRouteTests(unittest.TestCase):
    def _with_jobs_dir(self, jobs_dir: str):
        previous_jobs_dir = os.environ.get("JOBS_DIR")
        os.environ["JOBS_DIR"] = jobs_dir
        return previous_jobs_dir

    def _restore_jobs_dir(self, previous_jobs_dir: str | None) -> None:
        if previous_jobs_dir is None:
            os.environ.pop("JOBS_DIR", None)
        else:
            os.environ["JOBS_DIR"] = previous_jobs_dir

    def test_copy_pipeline_route_copies_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                create_pipeline_from_modules(
                    pipeline_name="source_pipeline",
                    module_specs=[
                        {"module": "http_get", "params": {"endpoint": "https://one.example"}},
                        {"module": "write_to_csv", "params": {"file_name": "first.csv"}},
                        {"module": "write_to_csv", "params": {"file_name": "second.csv"}},
                    ],
                    pipelines_dir=tmpdir,
                )
                set_pipeline_schedule(
                    pipeline_name="source_pipeline",
                    cron="*/5 * * * *",
                    pipelines_dir=tmpdir,
                )

                app = create_app()
                app.testing = True
                client = app.test_client()
                response = client.post(
                    "/pipelines/source_pipeline/copy",
                    json={"targetPipelineName": "copied_pipeline"},
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            self.assertEqual(response.status_code, 201)
            payload = response.get_json()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["pipeline"], "copied_pipeline")
            self.assertEqual(payload["sourcePipeline"], "source_pipeline")

            copied_config = load_config(str(Path(tmpdir) / "copied_pipeline.yaml"))
            self.assertEqual(copied_config["jobs"][0]["job"], "copied_pipeline")
            self.assertEqual(
                [asset["module"] for asset in copied_config["jobs"][0]["assets"]],
                ["http_get", "write_to_csv", "write_to_csv"],
            )
            self.assertEqual(
                copied_config["jobs"][0]["schedule"],
                {"cron": "*/5 * * * *", "active": True},
            )

    def test_copy_pipeline_route_rejects_missing_target_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                create_pipeline_from_modules(
                    pipeline_name="source_pipeline",
                    module_specs=["http_get"],
                    pipelines_dir=tmpdir,
                )

                app = create_app()
                app.testing = True
                client = app.test_client()
                response = client.post("/pipelines/source_pipeline/copy", json={})
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            self.assertEqual(response.status_code, 400)
            self.assertIn("targetPipelineName", response.get_json()["error"])

    def test_copy_pipeline_route_returns_conflict_for_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                create_pipeline_from_modules(
                    pipeline_name="source_pipeline",
                    module_specs=["http_get"],
                    pipelines_dir=tmpdir,
                )
                create_pipeline_from_modules(
                    pipeline_name="existing_pipeline",
                    module_specs=["json_mapper"],
                    pipelines_dir=tmpdir,
                )

                app = create_app()
                app.testing = True
                client = app.test_client()
                response = client.post(
                    "/pipelines/source_pipeline/copy",
                    json={"targetPipelineName": "existing_pipeline"},
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            self.assertEqual(response.status_code, 409)
            self.assertIn("already exists", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()

