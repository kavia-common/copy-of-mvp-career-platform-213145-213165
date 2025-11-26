"""Database setup: SQLAlchemy engine, session, and Base.

This module configures the database connection for the backend API. By default, it
uses a local SQLite database file to avoid needing an external DB during development
and tests.

Environment variables:
- DB_URL: Optional. Full SQLAlchemy URL. Defaults to SQLite file in current working directory.
- SQLITE_PATH: Optional. Path to the SQLite file (used only if DB_URL is not set).
"""

import os
from typing import Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from a .env file if present
load_dotenv()

# Default to a local SQLite file for development/testing
DEFAULT_SQLITE_PATH = os.getenv("SQLITE_PATH", "./career_platform.db")
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

def _ensure_sqlite_parent_dir(db_url: str) -> None:
    """
    Ensure the parent directory for the SQLite DB file exists (no-op for memory DB or non-sqlite).
    """
    if not db_url.startswith("sqlite"):
        return

    # Only handle typical file URLs, ignore in-memory DB (":memory:")
    prefix = "sqlite:///"
    if db_url.startswith(prefix):
        db_file = db_url[len(prefix):]
    else:
        # e.g., "sqlite+pysqlite:///" still works with splitting on last occurrence
        db_file = db_url.split("sqlite:///")[-1]

    if not db_file or db_file == ":memory:":
        return

    abs_path = os.path.abspath(os.path.expanduser(db_file))
    parent = os.path.dirname(abs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

# SQLite requires check_same_thread=False for usage with FastAPI/Uvicorn workers
connect_args: Dict[str, object] = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Make sure the directory for the SQLite file exists before opening the engine
    _ensure_sqlite_parent_dir(SQLALCHEMY_DATABASE_URL)

# Create engine and session factory
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Declarative Base for SQLAlchemy models
Base = declarative_base()
