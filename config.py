import os
from urllib.parse import urlparse

class Config:
    # Secret key for sessions and CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    # Default: PostgreSQL (from DATABASE_URL) or fallback SQLite
    _default_db = "sqlite:///skillswap.db"
    db_url = os.environ.get("DATABASE_URL", _default_db)

    # Fix Heroku/Render format (SQLAlchemy 2.x requires psycopg driver)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional: Pagination defaults for explore/search results
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", 10))

    # Optional: enable debug mode from env (default off in prod)
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
