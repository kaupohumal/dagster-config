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
Then run:

```cd dagster-config-server```

```pip install -r requirements.txt```

```python3 app.py```

## UI

```cd dagster-config-ui```

```yarn install```

```yarn quasar dev```