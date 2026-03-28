import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=False)

from server.create_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)