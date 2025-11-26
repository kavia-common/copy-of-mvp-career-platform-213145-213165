"""Role adjacency tests covering service JSON passthrough and local fallback behavior."""
from __future__ import annotations

import pytest

from src.models.role import Role
from src.models.competency import Competency
from src.models.role_competency import RoleCompetency
import src.services.role_mapping_client as mapping_client


def _auth_headers(client):
    email = "adjuser@example.com"
    password = "Passw0rd!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Adj User"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_roles_and_mappings(db_session):
    # Base roles
    r1 = Role(name="Chief Architect", description="R1")
    r2 = Role(name="CTO", description="R2")
    r3 = Role(name="VP Engineering", description="R3")
    db_session.add_all([r1, r2, r3])
    db_session.flush()

    # Competencies
    a = Competency(name="Architecture Strategy")
    b = Competency(name="Leadership")
    c = Competency(name="Finance")
    d = Competency(name="Cloud")
    db_session.add_all([a, b, c, d])
    db_session.flush()

    # R1: A=3, B=2
    db_session.add_all(
        [RoleCompetency(role_id=r1.id, competency_id=a.id, required_level=3),
         RoleCompetency(role_id=r1.id, competency_id=b.id, required_level=2)]
    )
    # R2: A=3, B=2, C=1 (more similar to R1)
    db_session.add_all(
        [RoleCompetency(role_id=r2.id, competency_id=a.id, required_level=3),
         RoleCompetency(role_id=r2.id, competency_id=b.id, required_level=2),
         RoleCompetency(role_id=r2.id, competency_id=c.id, required_level=1)]
    )
    # R3: D=1 (less similar)
    db_session.add(RoleCompetency(role_id=r3.id, competency_id=d.id, required_level=1))
    db_session.commit()
    return r1, r2, r3


def test_role_adjacency_service_passthrough(client, db_session):
    headers = _auth_headers(client)
    r1, _, _ = _seed_roles_and_mappings(db_session)

    # With default conftest monkeypatch, service returns zero items
    r = client.get("/api/v1/role-adjacency", headers=headers, params={"role": r1.name})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["role"] == r1.name
    assert data["total"] == 0
    assert isinstance(data["items"], list)


def test_role_adjacency_local_fallback_items(client, db_session, monkeypatch: pytest.MonkeyPatch):
    headers = _auth_headers(client)
    r1, r2, r3 = _seed_roles_and_mappings(db_session)

    # Force service to be unavailable to trigger local fallback
    from src.services.role_mapping_client import MappingServiceUnavailable

    def _raise_unavailable(*args, **kwargs):
        raise MappingServiceUnavailable("unavailable")

    monkeypatch.setattr(mapping_client, "get_adjacent_roles", _raise_unavailable, raising=True)

    r = client.get("/api/v1/role-adjacency", headers=headers, params={"role": r1.name, "limit": 5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["role"] == r1.name
    assert data["total"] >= 1
    # expect CTO (r2) to be more similar to CA (r1) than VP Eng (r3)
    if data["items"]:
        assert data["items"][0]["role"] in {r2.name, r1.name, r3.name}  # sanity
        # r2 should be present somewhere
        roles = [it["role"] for it in data["items"]]
        assert r2.name in roles


def test_role_adjacency_details_local_fallback(client, db_session, monkeypatch: pytest.MonkeyPatch):
    headers = _auth_headers(client)
    r1, r2, _ = _seed_roles_and_mappings(db_session)

    # Force details endpoint to fallback
    from src.services.role_mapping_client import MappingServiceUnavailable

    def _raise_unavailable_details(*args, **kwargs):
        raise MappingServiceUnavailable("unavailable")

    monkeypatch.setattr(mapping_client, "get_adjacency_details", _raise_unavailable_details, raising=True)

    r = client.get("/api/v1/role-adjacency/details", headers=headers, params={"current_role": r1.name, "target_role": r2.name})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["currentRole"] == r1.name
    assert data["targetRole"] == r2.name
    assert "shared" in data and isinstance(data["shared"], list)
