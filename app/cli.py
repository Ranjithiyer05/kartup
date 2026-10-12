import getpass

import click
from werkzeug.security import generate_password_hash

from .extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create database tables (safe to run repeatedly)."""
        db.create_all()
        click.echo("Database tables are ready.")

    @app.cli.command("hash-password")
    def hash_password():
        """Generate a value for ADMIN_PASSWORD_HASH."""
        password = getpass.getpass("Admin password: ")
        if password != getpass.getpass("Repeat password: "):
            raise click.ClickException("Passwords do not match.")
        if len(password) < 10:
            raise click.ClickException("Use at least 10 characters.")
        click.echo(generate_password_hash(password))
