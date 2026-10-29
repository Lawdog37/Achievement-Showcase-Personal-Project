"""Database connection: one engine for the app, sessions handed out per task."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

IS_SQLITE = DATABASE_URL.startswith("sqlite")

# pool_pre_ping: before reusing a connection, check it's still alive. Postgres
# (or the network) can quietly close connections that sat idle for a while.
engine = create_engine(DATABASE_URL, pool_pre_ping=not IS_SQLITE)
SessionLocal = sessionmaker(bind=engine)


# SQLite ignores foreign keys unless you switch them on for every connection
@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        # WAL mode lets the API read while a sync is writing
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
