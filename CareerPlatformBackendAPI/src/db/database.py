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

# SQLite requires check_same_thread=False for usage with FastAPI/Uvicorn workers
connect_args: Dict[str, object] = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine and session factory
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Declarative Base for SQLAlchemy models
Base = declarative_base()
