"""Health check endpoint tests."""
from __future__ import annotations


def test_health(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("message") == "Healthy"
