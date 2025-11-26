"""Authentication flow tests: register, login, profile."""
from __future__ import annotations

import uuid


def test_auth_register_login_profile(client):
    # Unique email for isolation
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "Passw0rd!"

    # Register
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201
    user = r.json()
    assert user["email"] == email
    assert user["is_admin"] is False

    # Login
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()
    assert "access_token" in token and token["access_token"]
    assert token.get("token_type", "bearer") == "bearer"

    # Profile (authorized)
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    r = client.get("/api/v1/auth/profile", headers=headers)
    assert r.status_code == 200
    prof = r.json()
    assert prof["email"] == email
    assert prof["is_admin"] is False

    # Unauthorized access
    r = client.get("/api/v1/auth/profile")
    assert r.status_code == 401
