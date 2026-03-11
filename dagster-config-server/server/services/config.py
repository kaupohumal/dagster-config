from __future__ import annotations

import os


def get_jobs_dir() -> str:
    jobs_dir = os.environ.get("JOBS_DIR")
    if not jobs_dir:
        raise EnvironmentError("JOBS_DIR environment variable is not set.")
    return jobs_dir

