from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import get_dagster_auth_header, get_dagster_graphql_url


FIND_PIPELINE_SELECTOR_QUERY = """
query FindPipelineSelector {
  repositoriesOrError {
    __typename
    ... on RepositoryConnection {
      nodes {
        name
        location {
          name
        }
        pipelines {
          name
        }
      }
    }
  }
}
"""


LAUNCH_PIPELINE_MUTATION = """
mutation LaunchPipeline($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    __typename
    ... on LaunchRunSuccess {
      run {
        runId
        status
      }
    }
  }
}
"""


GET_RUN_STATUS_QUERY = """
query GetRunStatus($runId: ID!) {
  runOrError(runId: $runId) {
    __typename
    ... on Run {
      runId
      status
    }
    ... on RunNotFoundError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
"""


@dataclass
class DagsterRunResult:
    ok: bool
    run_id: str | None = None
    status: str | None = None
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "runId": self.run_id,
            "status": self.status,
            "errorType": self.error_type,
            "error": self.error,
        }


class DagsterGraphQLError(Exception):
    pass


def _post_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    url = get_dagster_graphql_url()
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    auth_header = get_dagster_auth_header()
    if auth_header:
        headers[auth_header[0]] = auth_header[1]

    request = Request(url=url, data=payload, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise DagsterGraphQLError(f"Dagster API HTTP {e.code}: {body}") from e
    except URLError as e:
        raise DagsterGraphQLError(f"Failed to connect to Dagster API: {e.reason}") from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DagsterGraphQLError("Dagster API returned invalid JSON.") from e

    graphql_errors = data.get("errors") or []
    if graphql_errors:
        first = graphql_errors[0]
        message = first.get("message", "Unknown GraphQL error") if isinstance(first, dict) else str(first)
        raise DagsterGraphQLError(f"Dagster GraphQL error: {message}")

    return data.get("data") or {}


def _resolve_pipeline_selector(pipeline_name: str) -> dict[str, str]:
    data = _post_graphql(FIND_PIPELINE_SELECTOR_QUERY, {})
    repositories_or_error = data.get("repositoriesOrError") or {}

    if repositories_or_error.get("__typename") != "RepositoryConnection":
        typename = repositories_or_error.get("__typename", "Unknown")
        raise DagsterGraphQLError(f"Unexpected Dagster response: {typename}")

    matches: list[dict[str, str]] = []
    for node in repositories_or_error.get("nodes") or []:
        pipelines = node.get("pipelines") or []
        has_pipeline = any(item.get("name") == pipeline_name for item in pipelines if isinstance(item, dict))
        if not has_pipeline:
            continue

        repository_name = node.get("name")
        location = node.get("location") or {}
        location_name = location.get("name")
        if repository_name and location_name:
            matches.append(
                {
                    "repositoryName": repository_name,
                    "repositoryLocationName": location_name,
                    "pipelineName": pipeline_name,
                }
            )

    if not matches:
        raise DagsterGraphQLError(f"Pipeline '{pipeline_name}' was not found in Dagster repositories.")
    if len(matches) > 1:
        raise DagsterGraphQLError(
            f"Pipeline '{pipeline_name}' is ambiguous across repositories."
        )

    return matches[0]


def trigger_pipeline_run(
    pipeline_name: str,
    run_config_data: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> DagsterRunResult:
    selector = _resolve_pipeline_selector(pipeline_name)

    execution_params = {
        "selector": selector,
        "runConfigData": run_config_data or {},
        "executionMetadata": {
            "tags": [{"key": key, "value": value} for key, value in (tags or {}).items()],
        },
    }

    data = _post_graphql(LAUNCH_PIPELINE_MUTATION, {"executionParams": execution_params})
    launch_result = data.get("launchPipelineExecution") or {}
    typename = launch_result.get("__typename", "Unknown")

    if typename == "LaunchRunSuccess":
        run = launch_result.get("run") or {}
        return DagsterRunResult(ok=True, run_id=run.get("runId"), status=run.get("status"))

    return DagsterRunResult(
        ok=False,
        error_type=typename,
        error=f"Dagster rejected run launch: {typename}",
    )


def get_run_status(run_id: str) -> DagsterRunResult:
    data = _post_graphql(GET_RUN_STATUS_QUERY, {"runId": run_id})
    run_or_error = data.get("runOrError") or {}
    typename = run_or_error.get("__typename", "Unknown")

    if typename == "Run":
        return DagsterRunResult(
            ok=True,
            run_id=run_or_error.get("runId") or run_id,
            status=run_or_error.get("status"),
        )

    message = run_or_error.get("message") if isinstance(run_or_error, dict) else None
    return DagsterRunResult(
        ok=False,
        run_id=run_id,
        error_type=typename,
        error=message or f"Failed to fetch run status: {typename}",
    )


