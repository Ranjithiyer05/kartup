import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD_HASH": generate_password_hash("correct-horse-battery"),
        "ADMIN_PASSWORD": None,
    })
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
