import sqlite3

from app.core.config import settings


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a simple SQLite connection placeholder."""
    target_path = db_path or settings.SQLITE_DB_PATH
    # TODO: Replace with proper database session management when persistence is added.
    return sqlite3.connect(target_path)
