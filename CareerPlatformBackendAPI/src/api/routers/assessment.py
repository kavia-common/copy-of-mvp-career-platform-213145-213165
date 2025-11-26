"""Assessment routes: submit competency levels."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.assessment import Assessment
from src.models.audit import AuditLog
from src.models.user import User
from src.schemas.assessment import AssessmentCreate, AssessmentRead

router = APIRouter(prefix="/api/v1", tags=["Assessments"])


# PUBLIC_INTERFACE
@router.post(
    "/competency-assessment",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user competency assessment",
    description="Submit a set of competency levels for the current user.",
)
def submit_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentRead:
    """Persist an Assessment for the current user."""
    levels: Dict[str, int] = {str(item.competency_id): item.level for item in payload.competencies}

    record = Assessment(
        user_id=current_user.id,
        target_role_id=payload.target_role_id,
        competency_levels=levels,
    )
    db.add(record)
    db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="assessment_submit",
            entity_type="Assessment",
            entity_id=str(record.id),
            details={"target_role_id": payload.target_role_id, "num_competencies": len(levels)},
        )
    )
    db.commit()
    db.refresh(record)
    return AssessmentRead.model_validate(record)
