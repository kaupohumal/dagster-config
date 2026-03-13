import os
from dotenv import load_dotenv

_base_dir = os.path.dirname(__file__)
for _env_file_name in (".env.local", ".env"):
    _env_path = os.path.join(_base_dir, _env_file_name)
    if os.path.exists(_env_path):
        load_dotenv(dotenv_path=_env_path, override=False)

from server.create_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)