import os

from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(app.instance_path, exist_ok=True)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "sqlite:///" + os.path.join(app.instance_path, "kartup.db")
        )

    if not app.config.get("SECRET_KEY"):
        if app.debug or app.testing or os.environ.get("FLASK_DEBUG") == "1":
            app.config["SECRET_KEY"] = "dev-only-insecure-key"
        else:
            raise RuntimeError("SECRET_KEY environment variable must be set in production.")

    db.init_app(app)

    from . import models  # noqa: F401  (register models)
    from .admin import admin_bp
    from .public import public_bp
    from .cli import register_cli

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    register_cli(app)

    # Idempotent: creates the submissions table if it does not exist yet.
    with app.app_context():
        db.create_all()
        # Drop pooled connections so forked Gunicorn workers open their own.
        db.engine.dispose()

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; img-src 'self' data:; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        return response

    return app
