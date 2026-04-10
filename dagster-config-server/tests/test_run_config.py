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

run_config_service = importlib.import_module("server.services.run_config")
yaml_loader = importlib.import_module("server.services.yaml_loader")

apply_arcgis_resource_config = run_config_service.apply_arcgis_resource_config
apply_minio_resource_config = run_config_service.apply_minio_resource_config
save_config = yaml_loader.save_config


class RunConfigTests(unittest.TestCase):
    def _with_jobs_dir(self, jobs_dir: str):
        previous_jobs_dir = os.environ.get("JOBS_DIR")
        os.environ["JOBS_DIR"] = jobs_dir
        return previous_jobs_dir

    def _restore_jobs_dir(self, previous_jobs_dir: str | None) -> None:
        if previous_jobs_dir is None:
            os.environ.pop("JOBS_DIR", None)
        else:
            os.environ["JOBS_DIR"] = previous_jobs_dir

    def test_non_arcgis_pipeline_skips_arcgis_resource_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "no_arcgis.yaml"),
                {
                    "jobs": [
                        {
                            "job": "no_arcgis",
                            "assets": [
                                {"asset": "get_data", "module": "http_get", "params": {"endpoint": "https://x"}},
                                {"asset": "write_data", "module": "write_to_csv", "ins": "get_data"},
                            ],
                        }
                    ]
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                merged = apply_arcgis_resource_config("no_arcgis", None)
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            self.assertEqual(merged, {})

    def test_arcgis_pipeline_merges_resource_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "with_arcgis.yaml"),
                {
                    "resources": [
                        {
                            "resource": "ArcGIS",
                            "name": "arcGIS",
                            "params": {
                                "token": "ARCGIS_API",
                                "feature_service_address": "gis.example",
                            },
                        }
                    ],
                    "jobs": [
                        {
                            "job": "with_arcgis",
                            "assets": [
                                {"asset": "send", "module": "send_to_arcgis"},
                            ],
                        }
                    ],
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                merged = apply_arcgis_resource_config(
                    "with_arcgis",
                    run_config_data={"resources": {"arcGIS": {"config": {"feature_service_address": "override"}}}},
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            config = merged["resources"]["arcGIS"]["config"]
            self.assertEqual(config["token"], "ARCGIS_API")
            self.assertEqual(config["feature_service_address"], "override")

    def test_arcgis_pipeline_without_resource_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "missing_arcgis_resource.yaml"),
                {
                    "jobs": [
                        {
                            "job": "missing_arcgis_resource",
                            "assets": [
                                {"asset": "send", "module": "send_to_arcgis"},
                            ],
                        }
                    ]
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                with self.assertRaises(LookupError):
                    apply_arcgis_resource_config("missing_arcgis_resource", None)
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

    def test_arcgis_pipeline_preserves_yaml_token_when_run_config_token_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "with_arcgis_token.yaml"),
                {
                    "resources": [
                        {
                            "resource": "ArcGIS",
                            "name": "arcGIS",
                            "params": {
                                "token": "persisted-token",
                                "feature_service_address": "gis.example",
                            },
                        }
                    ],
                    "jobs": [
                        {
                            "job": "with_arcgis_token",
                            "assets": [
                                {"asset": "send", "module": "send_to_arcgis"},
                            ],
                        }
                    ],
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                merged = apply_arcgis_resource_config(
                    "with_arcgis_token",
                    run_config_data={
                        "resources": {
                            "arcGIS": {
                                "config": {
                                    "token": "",
                                    "feature_service_address": "override",
                                }
                            }
                        }
                    },
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            config = merged["resources"]["arcGIS"]["config"]
            self.assertEqual(config["token"], "persisted-token")
            self.assertEqual(config["feature_service_address"], "override")

    def test_minio_pipeline_merges_resource_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "with_minio.yaml"),
                {
                    "resources": [
                        {
                            "resource": "MinIO",
                            "name": "minio",
                            "params": {
                                "host": "minio.local",
                                "access_key": "MINIO_ACCESS_KEY",
                                "secret_key": "MINIO_SECRET_KEY",
                            },
                        }
                    ],
                    "jobs": [
                        {
                            "job": "with_minio",
                            "assets": [
                                {"asset": "write", "module": "write_to_csv"},
                            ],
                        }
                    ],
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                merged = apply_minio_resource_config(
                    "with_minio",
                    run_config_data={
                        "resources": {
                            "minio": {
                                "config": {
                                    "host": "override.local",
                                }
                            }
                        }
                    },
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            config = merged["resources"]["minio"]["config"]
            self.assertEqual(config["host"], "override.local")
            self.assertEqual(config["access_key"], "MINIO_ACCESS_KEY")
            self.assertEqual(config["secret_key"], "MINIO_SECRET_KEY")

    def test_minio_pipeline_preserves_yaml_secret_when_run_config_secret_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            save_config(
                str(Path(tmpdir) / "with_minio_secret.yaml"),
                {
                    "resources": [
                        {
                            "resource": "MinIO",
                            "name": "minio",
                            "params": {
                                "host": "minio.local",
                                "access_key": "MINIO_ACCESS_KEY",
                                "secret_key": "persisted-secret",
                            },
                        }
                    ],
                    "jobs": [
                        {
                            "job": "with_minio_secret",
                            "assets": [
                                {"asset": "write", "module": "write_to_csv"},
                            ],
                        }
                    ],
                },
            )

            previous_jobs_dir = self._with_jobs_dir(tmpdir)
            try:
                merged = apply_minio_resource_config(
                    "with_minio_secret",
                    run_config_data={
                        "resources": {
                            "minio": {
                                "config": {
                                    "secret_key": "",
                                }
                            }
                        }
                    },
                )
            finally:
                self._restore_jobs_dir(previous_jobs_dir)

            config = merged["resources"]["minio"]["config"]
            self.assertEqual(config["secret_key"], "persisted-secret")


if __name__ == "__main__":
    unittest.main()

