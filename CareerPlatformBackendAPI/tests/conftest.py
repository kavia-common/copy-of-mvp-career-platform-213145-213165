"""Pytest fixtures for the CareerPlatformBackendAPI.

- Uses a SQLite test database file (unique per test session) via DB_URL env var.
- Provides FastAPI TestClient as 'client'.
- Provides a SQLAlchemy Session as 'db_session' when needed.
- Mocks the Node RoleMappingService client functions to avoid network during tests.
"""
from __future__ import annotations

import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _configure_environment(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Configure environment for tests before app import.

    - Set DB_URL to a SQLite file under the test temp directory.
    - Disable JSON seeding and sample data seeding.
    - Provide a deterministic JWT secret for tests.
    - Point mapping service URL at a non-routable target to ensure no accidental calls.
    """
    # Ensure project root is on sys.path for 'src.' imports
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this_dir, ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Database: use a file-based SQLite DB for the whole session
    tmp_dir = tmp_path_factory.mktemp("testdb")
    db_file = os.path.join(str(tmp_dir), "test.db")
    os.environ.setdefault("DB_URL", f"sqlite:///{db_file}")
    os.environ.setdefault("SEED_FROM_JSON", "0")
    os.environ.setdefault("SEED_SAMPLE_DATA", "0")

    # JWT and mapping client defaults
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
    os.environ.setdefault("MAPPING_SERVICE_URL", "http://localhost:0")
    os.environ.setdefault("MAPPING_HTTP_TIMEOUT_SECONDS", "0.1")
    os.environ.setdefault("MAPPING_HTTP_RETRIES", "0")


@pytest.fixture(scope="session")
def app():
    """Import and return the FastAPI app after environment is configured."""
    from src.api.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def client(app) -> Generator[TestClient, None, None]:
    """Yield a TestClient that manages FastAPI startup/shutdown for each test."""
    with TestClient(app) as tc:
        yield tc


@pytest.fixture()
def db_session():
    """Provide a SQLAlchemy session for direct DB interactions if needed."""
    from src.db.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def mock_mapping_client(monkeypatch: pytest.MonkeyPatch):
    """Prevent external network calls to the Node RoleMappingService.

    Provides simple, deterministic return values for client functions.
    """
    from typing import Any, Dict, Optional

    # Lazy import of module to patch
    import src.services.role_mapping_client as mapping_client

    def _fake_get_adjacent_roles(role_name: str, limit: int = 10, min_score: float = 0.0) -> Dict[str, Any]:
        return {"role": role_name, "total": 0, "items": []}

    def _fake_get_adjacency_details(current_role: str, target_role: str) -> Dict[str, Any]:
        # Minimal shape that matches AdjacencyDetailsResponse
        return {
            "currentRole": current_role,
            "targetRole": target_role,
            "score": 0.0,
            "shared": [],
            "missingInCurrent": [],
            "extraInCurrent": [],
            "stats": {
                "sharedCompetencies": 0,
                "missingInCurrent": 0,
                "extraInCurrent": 0,
            },
        }

    def _fake_get_competency_map_for_role(role_name: str) -> Optional[Dict[str, int]]:
        return None

    monkeypatch.setattr(mapping_client, "get_adjacent_roles", _fake_get_adjacent_roles, raising=True)
    monkeypatch.setattr(mapping_client, "get_adjacency_details", _fake_get_adjacency_details, raising=True)
    monkeypatch.setattr(mapping_client, "get_competency_map_for_role", _fake_get_competency_map_for_role, raising=True)
