"""Development plan routes: generate plans and export stubs."""

from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.audit import AuditLog
from src.models.development_plan import DevelopmentPlan
from src.models.user import User
from src.schemas.development_plan import (
    DevelopmentPlanCreate,
    DevelopmentPlanRead,
    PlanExportRequest,
    PlanExportResponse,
    PlanStep,
)

router = APIRouter(prefix="/api/v1", tags=["Development Plans"])


def _generate_steps_from_gaps(gaps: list) -> List[PlanStep]:
    steps: List[PlanStep] = []
    for gap in gaps:
        comp_name = gap.competency_name
        delta = gap.required_level - gap.current_level
        steps.append(
            PlanStep(
                description=f"Deepen {comp_name} by {delta} level(s) via structured learning",
                action_type="Learn",
                resource=f"https://www.example.com/learn/{comp_name.replace(' ', '-').lower()}",
            )
        )
        steps.append(
            PlanStep(
                description=f"Find a mentor to accelerate {comp_name} growth",
                action_type="Mentor",
                resource=None,
            )
        )
        steps.append(
            PlanStep(
                description=f"Apply {comp_name} in a real project or initiative",
                action_type="Practice",
                resource=None,
            )
        )
    return steps


# PUBLIC_INTERFACE
@router.post(
    "/development-plan",
    response_model=DevelopmentPlanRead,
    summary="Generate development plan",
    description="Create a simple development plan based on computed gaps.",
)
def generate_development_plan(
    payload: DevelopmentPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DevelopmentPlanRead:
    """Generate and persist a development plan."""
    steps = _generate_steps_from_gaps(payload.gaps)
    steps_dicts = [s.model_dump() for s in steps]

    record = DevelopmentPlan(
        user_id=current_user.id,
        target_role_id=payload.target_role_id,
        steps=steps_dicts,
    )
    db.add(record)
    db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="dev_plan_generate",
            entity_type="DevelopmentPlan",
            entity_id=str(record.id),
            details={"steps": len(steps_dicts)},
        )
    )
    db.commit()
    db.refresh(record)
    return DevelopmentPlanRead.model_validate(record)


# PUBLIC_INTERFACE
@router.post(
    "/development-plan/export",
    response_model=PlanExportResponse,
    summary="Export plan (PDF/link)",
    description="Stub export endpoint that returns a link to the plan export.",
)
def export_development_plan(
    payload: PlanExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanExportResponse:
    """Return a stub URL for the exported plan (no real file generated)."""
    # Determine plan ID: use requested or most recent plan
    plan_id = payload.plan_id
    if plan_id is None:
        record = (
            db.query(DevelopmentPlan).filter(DevelopmentPlan.user_id == current_user.id).order_by(DevelopmentPlan.id.desc()).first()
        )
        if record:
            plan_id = record.id

    base_url = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:3001")
    export_url = f"{base_url}/static/devplans/{plan_id or 'latest'}.{payload.format}"
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="dev_plan_export",
            entity_type="DevelopmentPlan",
            entity_id=str(plan_id) if plan_id else None,
            details={"format": payload.format},
        )
    )
    db.commit()
    return PlanExportResponse(url=export_url)
