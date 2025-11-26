"""End-to-end tests for gap analysis and development plan generation."""
from __future__ import annotations

from typing import Dict, List

from src.models.role import Role
from src.models.competency import Competency
from src.models.role_competency import RoleCompetency


def _auth_headers(client) -> Dict[str, str]:
    email = "gapuser@example.com"
    password = "Passw0rd!"
    # Register (idempotent for test run)
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Gap User"})
    # Login
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_gap_analysis_and_plan_generation(client, db_session):
    headers = _auth_headers(client)

    # Setup roles and competencies
    r2 = Role(name="Target CTO", description="Target role")
    r1 = Role(name="Current CA", description="Current role")
    db_session.add_all([r1, r2])
    db_session.flush()

    comp_a = Competency(name="Architecture Strategy", definition="Ability to define arch strategy")
    comp_b = Competency(name="Leadership", definition="People leadership")
    comp_c = Competency(name="Finance", definition="Budgeting and finance")
    db_session.add_all([comp_a, comp_b, comp_c])
    db_session.flush()

    # Required levels for target role (r2): A=3, B=2, C=1
    db_session.add_all(
        [
            RoleCompetency(role_id=r2.id, competency_id=comp_a.id, required_level=3),
            RoleCompetency(role_id=r2.id, competency_id=comp_b.id, required_level=2),
            RoleCompetency(role_id=r2.id, competency_id=comp_c.id, required_level=1),
        ]
    )
    # Current role requirements (r1) not used by gap-analysis route except for fallback, but add some data anyway
    db_session.add(RoleCompetency(role_id=r1.id, competency_id=comp_a.id, required_level=1))
    db_session.commit()

    # Current user's competency levels (below target requirements to force gaps)
    current_levels: List[Dict] = [
        {"competency_id": comp_a.id, "level": 1},
        {"competency_id": comp_b.id, "level": 1},
        # comp_c omitted -> treated as 0 for current level
    ]
    payload = {"target_role_id": r2.id, "current_competencies": current_levels}

    # Perform gap analysis (service is stubbed in conftest to None -> fallback to DB)
    r = client.post("/api/v1/gap-analysis", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["target_role_id"] == r2.id
    assert result["total_gaps"] >= 2
    gaps = result["gaps"]
    # Ensure expected gaps present
    names = {g["competency_name"] for g in gaps}
    assert "Architecture Strategy" in names
    assert "Leadership" in names or "Finance" in names

    # Generate development plan based on gaps
    r = client.post(
        "/api/v1/development-plan",
        headers=headers,
        json={"target_role_id": r2.id, "gaps": gaps},
    )
    assert r.status_code == 200, r.text
    plan = r.json()
    assert plan["user_id"] is not None
    assert plan["target_role_id"] == r2.id
    # Each gap yields 3 plan steps (Learn, Mentor, Practice)
    assert len(plan["steps"]) == 3 * len(gaps)
    # Export stub
    r = client.post("/api/v1/development-plan/export", headers=headers, json={"format": "link"})
    assert r.status_code == 200
    assert "url" in r.json()
