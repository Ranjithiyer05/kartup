import os


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    # Normalise provider URLs (postgres:// or postgresql://) to the psycopg 3 driver.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1" if _database_url() else "0") == "1"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 2  # 2 hours
    MAX_CONTENT_LENGTH = 16 * 1024
