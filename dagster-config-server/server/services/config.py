from __future__ import annotations

import os


def get_jobs_dir() -> str:
    jobs_dir = os.environ.get("JOBS_DIR")
    if not jobs_dir:
        raise EnvironmentError("JOBS_DIR environment variable is not set.")
    return jobs_dir


def get_dagster_graphql_url() -> str:
    dagster_graphql_url = os.environ.get("DAGSTER_GRAPHQL_URL")
    if not dagster_graphql_url:
        raise EnvironmentError("DAGSTER_GRAPHQL_URL environment variable is not set.")
    return dagster_graphql_url


def get_dagster_auth_header() -> tuple[str, str] | None:
    token = os.environ.get("DAGSTER_API_TOKEN")
    if not token:
        return None

    header_name = os.environ.get("DAGSTER_AUTH_HEADER", "Authorization")
    token_prefix = os.environ.get("DAGSTER_AUTH_PREFIX", "Bearer")
    header_value = f"{token_prefix} {token}" if token_prefix else token
    return header_name, header_value


