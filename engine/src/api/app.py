from __future__ import annotations

from flask import Flask

from .routes import bp as api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
