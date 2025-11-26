"""Gap analysis routes: compute gaps against a target role."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.audit import AuditLog
from src.models.competency import Competency
from src.models.role_competency import RoleCompetency
from src.models.user import User
from src.schemas.assessment import CompetencyLevel
from src.schemas.development_plan import GapAnalysisRequest, GapAnalysisResult, GapItem

router = APIRouter(prefix="/api/v1", tags=["Gap Analysis"])


def _levels_to_map(items: List[CompetencyLevel]) -> Dict[int, int]:
    return {i.competency_id: i.level for i in items}


# PUBLIC_INTERFACE
@router.post(
    "/gap-analysis",
    response_model=GapAnalysisResult,
    summary="Perform gap analysis",
    description="Compute gaps between user current competencies and target role required levels.",
)
def perform_gap_analysis(
    payload: GapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GapAnalysisResult:
    """Compare current levels to required levels, returning competency gaps."""
    current_map = _levels_to_map(payload.current_competencies)
    rows = (
        db.query(Competency, RoleCompetency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .filter(RoleCompetency.role_id == payload.target_role_id)
        .all()
    )

    gaps: List[GapItem] = []
    for comp, rc in rows:
        current_level = int(current_map.get(comp.id, 0))
        if current_level < rc.required_level:
            gaps.append(
                GapItem(
                    competency_id=comp.id,
                    competency_name=comp.name,
                    current_level=current_level,
                    required_level=rc.required_level,
                )
            )

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="gap_analysis",
            entity_type="Role",
            entity_id=str(payload.target_role_id),
            details={"computed_gaps": len(gaps)},
        )
    )
    db.commit()

    return GapAnalysisResult(target_role_id=payload.target_role_id, gaps=gaps, total_gaps=len(gaps))
