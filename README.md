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

Set the required git environment variables in `dagster-config-server/.env.local`:

- `GIT_TOKEN` (personal access token with read/write access)

Then run:

```cd dagster-config-server```

```pip install -r requirements.txt```

```python3 app.py```

## UI

```cd dagster-config-ui```

```yarn install```

```yarn quasar dev```