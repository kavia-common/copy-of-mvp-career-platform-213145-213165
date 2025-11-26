"""Gap analysis routes: compute gaps against a target role."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.audit import AuditLog
from src.models.competency import Competency
from src.models.role import Role
from src.models.role_competency import RoleCompetency
from src.models.user import User
from src.schemas.assessment import CompetencyLevel
from src.schemas.development_plan import GapAnalysisRequest, GapAnalysisResult, GapItem
# Import the client module so pytest monkeypatch applies to it
import src.services.role_mapping_client as mapping_client
from src.services.role_mapping_client import MappingServiceUnavailable

router = APIRouter(prefix="/api/v1", tags=["Gap Analysis"])


def _levels_to_map(items: List[CompetencyLevel]) -> Dict[int, int]:
    return {i.competency_id: i.level for i in items}


def _required_map_from_db_by_role_id(db: Session, role_id: int) -> List[tuple[int, str, int]]:
    """Return a list of (competency_id, competency_name, required_level) tuples from local DB for the role_id."""
    rows = (
        db.query(Competency, RoleCompetency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .filter(RoleCompetency.role_id == role_id)
        .all()
    )
    out: List[tuple[int, str, int]] = []
    for comp, rc in rows:
        out.append((comp.id, comp.name, int(rc.required_level)))
    return out


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
    """Compare current levels to required levels, returning competency gaps.

    Integration:
    - Attempts to fetch required competency levels for the target role from the Node RoleMappingService.
    - On service unavailability or missing mapping, gracefully falls back to local DB mappings.
    """
    # Resolve role to name for service call
    role = db.query(Role).filter(Role.id == payload.target_role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target role not found")

    current_map = _levels_to_map(payload.current_competencies)

    # Try service first
    required_items: List[tuple[int, str, int]] = []
    used_service = False
    try:
        svc_map = mapping_client.get_competency_map_for_role(role.name)
        if svc_map:
            # svc_map: { name -> required_level }, map to DB competency ids by name
            names = list(svc_map.keys())
            if names:
                comps = db.query(Competency).filter(Competency.name.in_(names)).all()
                name_to_id = {c.name: c.id for c in comps}
                for name, level in svc_map.items():
                    comp_id = name_to_id.get(name)
                    if comp_id is not None:
                        required_items.append((comp_id, name, int(level)))
                used_service = True
    except MappingServiceUnavailable:
        used_service = False  # fall back below

    # Fallback to DB if service not used or did not yield items
    if not used_service or not required_items:
        required_items = _required_map_from_db_by_role_id(db, role.id)

    gaps: List[GapItem] = []
    for comp_id, comp_name, req_level in required_items:
        current_level = int(current_map.get(int(comp_id), 0))
        if current_level < req_level:
            gaps.append(
                GapItem(
                    competency_id=int(comp_id),
                    competency_name=comp_name,
                    current_level=current_level,
                    required_level=int(req_level),
                )
            )

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="gap_analysis",
            entity_type="Role",
            entity_id=str(payload.target_role_id),
            details={"computed_gaps": len(gaps), "source": "service" if used_service else "db"},
        )
    )
    db.commit()

    return GapAnalysisResult(target_role_id=payload.target_role_id, gaps=gaps, total_gaps=len(gaps))
