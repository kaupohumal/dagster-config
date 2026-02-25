from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .routes import api


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(api)

    return app
