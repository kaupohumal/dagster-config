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
```

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

## UI

```cd dagster-config-ui```

```yarn install```

```yarn quasar dev```