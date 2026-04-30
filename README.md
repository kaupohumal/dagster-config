# Dagster Pipeline Editor

This app allows editing Dagster pipelines using a UI.
Frontend server is in the dagster-config-ui directory and
backend is in the dagster-config-server directory.

# Prerequisites

- Dagster running from the [dagster-services](https://github.com/kaupohumal/dagster-services) and [dagster-user-code](https://github.com/kaupohumal/dagster-user-code) repositories,
- Python 3.14
- Yarn 1.22
- Node >=20

# Usage

## Backend

First, set the path to the directory containing Dagster job definition yaml files in the dagster-config-server/.env file.
Set the Dagster GraphQL endpoint as well.

Example `.env` for `dagster-config-server`:

```bash
JOBS_DIR=/absolute/path/to/jobs
DAGSTER_GRAPHQL_URL=http://localhost:3000/graphql
DAGSTER_UI_BASE_URL=http://localhost:3000
```

`DAGSTER_UI_BASE_URL` is optional. If omitted, backend derives it from `DAGSTER_GRAPHQL_URL` by removing `/graphql`. Set it explicitly when UI and GraphQL hosts differ.

Then run:

```cd dagster-config-server```

```pip install -r requirements.txt```

```python3 app.py```


## UI

```cd dagster-config-ui```

```yarn install```

```yarn quasar dev```

