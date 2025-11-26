"""Competencies routes: list competencies, optionally with role requirements."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.competency import Competency
from src.models.role_competency import RoleCompetency
from src.schemas.competency import CompetencyRead, CompetencyWithRequirement

router = APIRouter(prefix="/api/v1", tags=["Competencies"])


# PUBLIC_INTERFACE
@router.get(
    "/competencies",
    response_model=List[CompetencyRead],
    summary="List competencies",
    description="List all competencies. If role_id is provided, use /competencies/by-role instead to include required levels.",
)
def list_competencies(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CompetencyRead]:
    """List all competencies."""
    items = db.query(Competency).order_by(Competency.name.asc()).all()
    return [CompetencyRead.model_validate(x) for x in items]


# PUBLIC_INTERFACE
@router.get(
    "/competencies/by-role",
    response_model=List[CompetencyWithRequirement],
    summary="List competencies for a role with required levels",
    description="Return competencies along with required level for the given role.",
)
def list_competencies_by_role(
    role_id: int = Query(..., description="Role identifier"),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CompetencyWithRequirement]:
    """List competencies along with required levels for a role."""
    rows = (
        db.query(Competency, RoleCompetency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .filter(RoleCompetency.role_id == role_id)
        .all()
    )
    response: list[CompetencyWithRequirement] = []
    for comp, rc in rows:
        response.append(
            CompetencyWithRequirement(
                id=comp.id,
                name=comp.name,
                definition=comp.definition,
                category=comp.category,
                required_level=rc.required_level,
            )
        )
    return response
