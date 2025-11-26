"""Roles endpoint tests: create, list, read."""
from __future__ import annotations

import uuid


def test_roles_crud_minimal(client):
    # Create role
    role_name = f"Test Role {uuid.uuid4().hex[:6]}"
    desc = "Created by pytest"
    r = client.post("/api/v1/roles", json={"name": role_name, "description": desc})
    assert r.status_code == 201
    created = r.json()
    role_id = created["id"]
    assert created["name"] == role_name

    # List roles
    r = client.get("/api/v1/roles")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(it["id"] == role_id and it["name"] == role_name for it in items)

    # Get by ID
    r = client.get(f"/api/v1/roles/{role_id}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == role_id
    assert got["name"] == role_name
