"""Middleware tests for request-id propagation and CORS behavior."""
from __future__ import annotations


def test_request_id_propagation(client):
    rid = "test-req-123"
    r = client.get("/", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    # Response headers are case-insensitive
    assert r.headers.get("X-Request-ID") == rid


def test_request_id_generated_when_missing(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert r.headers["X-Request-ID"]


def test_cors_allows_default_localhost_origin(client):
    # Default app configuration allows localhost:3000
    origin = "http://localhost:3000"
    r = client.get("/", headers={"Origin": origin})
    # Starlette CORS will include allow-origin header when origin matches allowlist
    allow = r.headers.get("access-control-allow-origin") or r.headers.get("Access-Control-Allow-Origin")
    assert allow == origin
