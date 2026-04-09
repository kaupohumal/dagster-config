# Dagster Pipeline Editor

This app allows editing Dagster pipelines using a UI.
Frontend server is in the dagster-config-ui directory and
backend is in the dagster-config-server directory.

# Prerequisites

- Dagster running from the [dagster-services](https://github.com/kaupohumal/dagster-services) and [dagster-user-code](https://github.com/kaupohumal/dagster-user-code) repositories,
- Dagster pipeline yaml files in a local directory that's mounted to dagster-user-code and this app can access
- Python 3.14
- Yarn 1.22
- Node >=20

# Usage

## Backend

First, set the path to the directory containing Dagster job definition yaml files in the .env file.
Set the Dagster GraphQL endpoint as well.

Example `.env` for `dagster-config-server`:

```bash
JOBS_DIR=/absolute/path/to/jobs
DAGSTER_GRAPHQL_URL=http://localhost:3000/graphql
DAGSTER_UI_BASE_URL=http://localhost:3000
```

`DAGSTER_UI_BASE_URL` is optional. If omitted, backend derives it from `DAGSTER_GRAPHQL_URL` by removing `/graphql`. Set it explicitly when UI and GraphQL hosts differ.

Optional auth for Dagster API:

```bash
DAGSTER_API_TOKEN=your-token
DAGSTER_AUTH_HEADER=Authorization
DAGSTER_AUTH_PREFIX=Bearer
```

Then run:

```cd dagster-config-server```

```pip install -r requirements.txt```

```python3 app.py```

To launch a run from backend directly:

```bash
curl -X POST "http://localhost:5000/pipelines/<pipeline_name>/run" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Create a new pipeline from modules:

```bash
curl -X POST "http://localhost:5000/pipelines" \
  -H "Content-Type: application/json" \
  -d '{
    "pipelineName": "my_new_pipeline",
    "modules": [
      "http_get",
      "json_mapper",
      "write_to_csv"
    ]
  }'
```

Swap an asset module by asset index:

```bash
curl -X PATCH "http://localhost:5000/pipelines/my_new_pipeline/assets/2/module" \
  -H "Content-Type: application/json" \
  -d '{
    "targetModule": "send_to_arcgis",
    "preserveCompatibleParams": true,
    "dryRun": false
  }'
```

List supported modules and pipeline entries:

```bash
curl "http://localhost:5000/module-catalog"
curl "http://localhost:5000/pipelines/my_new_pipeline/module-entries"
```

Get or update one specific module config by module entry index:

```bash
curl "http://localhost:5000/pipelines/my_new_pipeline/modules/http_get/0"

curl -X PATCH "http://localhost:5000/pipelines/my_new_pipeline/modules/http_get/0" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://example.com/api",
    "params": [{"key": "page", "value": "1"}]
  }'
```

Add or remove modules in an existing pipeline:

```bash
curl -X POST "http://localhost:5000/pipelines/my_new_pipeline/assets" \
  -H "Content-Type: application/json" \
  -d '{
    "targetModule": "transform_to_arcgis_format",
    "insertIndex": 2
  }'

curl -X DELETE "http://localhost:5000/pipelines/my_new_pipeline/assets/2"
```

Run backend tests:

```bash
cd dagster-config-server
python3 -m unittest tests/test_modules_pipeline_builder.py
```

## UI

```cd dagster-config-ui```

```yarn install```

```yarn quasar dev```

Manual UI test flow:

1. Open `/pipelines` and click **Create pipeline**.
2. Enter a pipeline name, pick module order, and click **Create**.
3. Open the created pipeline page.
4. Use the module dropdown on an asset card and click **Swap**.
5. Confirm the card type updates and saved YAML reflects the module change.

