"""Role adjacency routes: suggest adjacent roles and show detailed comparison.

This router integrates with the Node RoleMappingService via a small HTTP client with
timeouts and retries. If the Node service is unavailable, the router falls back to
a local computation based on the database's role-competency mappings.

Endpoints:
- GET /api/v1/role-adjacency
- GET /api/v1/role-adjacency/details
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.models.competency import Competency
from src.models.role import Role
from src.models.role_competency import RoleCompetency
from src.schemas.role_mapping import (
    AdjacentRoleItem,
    AdjacentRolesResponse,
    AdjacencyDetailsResponse,
    AdjacencyExtra,
    AdjacencyMissing,
    AdjacencySharedCompetency,
    AdjacencyStats,
)
# Import the client module so pytest monkeypatching applies to our calls
import src.services.role_mapping_client as mapping_client
from src.services.role_mapping_client import MappingServiceUnavailable

router = APIRouter(prefix="/api/v1", tags=["Role Mapping"])


def _required_map_by_role_id(db: Session, role_id: int) -> Dict[str, int]:
    """Return { competency_name: required_level } for a role_id from local DB."""
    rows = (
        db.query(Competency, RoleCompetency)
        .join(RoleCompetency, RoleCompetency.competency_id == Competency.id)
        .filter(RoleCompetency.role_id == role_id)
        .all()
    )
    result: Dict[str, int] = {}
    for comp, rc in rows:
        result[comp.name] = int(rc.required_level)
    return result


def _weighted_jaccard(map_a: Dict[str, int], map_b: Dict[str, int]) -> float:
    """Weighted Jaccard over required levels: sum(min)/sum(max)."""
    keys = set(map_a.keys()) | set(map_b.keys())
    sum_min = 0
    sum_max = 0
    for k in keys:
        a = int(map_a.get(k, 0))
        b = int(map_b.get(k, 0))
        if a == 0 and b == 0:
            continue
        sum_min += min(a, b)
        sum_max += max(a, b)
    return (sum_min / sum_max) if sum_max else 0.0


def _local_adjacent_roles(
    db: Session, role_name: str, limit: int, min_score: float
) -> AdjacentRolesResponse:
    """Compute adjacent roles locally from DB mappings as a graceful fallback."""
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        # attempt to treat as integer ID if provided
        try:
            role_id_int = int(role_name)
            role = db.query(Role).filter(Role.id == role_id_int).first()
        except Exception:
            role = None
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Role not found: {role_name}"
        )

    map_a = _required_map_by_role_id(db, role.id)
    other_roles = db.query(Role).filter(Role.id != role.id).all()

    items: List[AdjacentRoleItem] = []
    set_a = set(map_a.keys())
    for other in other_roles:
        map_b = _required_map_by_role_id(db, other.id)
        score = _weighted_jaccard(map_a, map_b)
        set_b = set(map_b.keys())
        shared = len(set_a & set_b)
        missing_in_current = len(set_b - set_a)
        extra_in_current = len(set_a - set_b)
        items.append(
            AdjacentRoleItem(
                role=other.name,
                score=round(score + 1e-9, 2),
                sharedCompetencies=shared,
                missingInCurrent=missing_in_current,
                extraInCurrent=extra_in_current,
            )
        )
    items = [i for i in items if i.score >= min_score]
    items.sort(key=lambda x: x.score, reverse=True)
    items = items[:limit]
    return AdjacentRolesResponse(role=role.name, total=len(items), items=items)


def _local_adjacency_details(
    db: Session, current_role: str, target_role: str
) -> AdjacencyDetailsResponse:
    """Compute detailed adjacency locally from DB as a fallback."""
    a = db.query(Role).filter(Role.name == current_role).first()
    b = db.query(Role).filter(Role.name == target_role).first()
    if not a or not b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role not found: {current_role if not a else target_role}",
        )
    map_a = _required_map_by_role_id(db, a.id)
    map_b = _required_map_by_role_id(db, b.id)

    score = _weighted_jaccard(map_a, map_b)

    shared: List[AdjacencySharedCompetency] = []
    missing: List[AdjacencyMissing] = []
    extra: List[AdjacencyExtra] = []

    set_a = set(map_a.keys())
    set_b = set(map_b.keys())

    for comp in sorted(set_a & set_b):
        curr = int(map_a.get(comp, 0))
        targ = int(map_b.get(comp, 0))
        shared.append(
            AdjacencySharedCompetency(
                competency=comp, current_level=curr, target_level=targ, delta=(targ - curr)
            )
        )
    for comp in sorted(set_b - set_a):
        missing.append(AdjacencyMissing(competency=comp, target_level=int(map_b.get(comp, 0))))
    for comp in sorted(set_a - set_b):
        extra.append(AdjacencyExtra(competency=comp, current_level=int(map_a.get(comp, 0))))

    stats = AdjacencyStats(
        sharedCompetencies=len(shared),
        missingInCurrent=len(missing),
        extraInCurrent=len(extra),
    )
    return AdjacencyDetailsResponse(
        currentRole=a.name,
        targetRole=b.name,
        score=round(score + 1e-9, 2),
        shared=shared,
        missingInCurrent=missing,
        extraInCurrent=extra,
        stats=stats,
    )


# PUBLIC_INTERFACE
@router.get(
    "/role-adjacency",
    response_model=AdjacentRolesResponse,
    summary="Get adjacent role suggestions",
    description=(
        "Return suggested adjacent roles for a given role using the Node RoleMappingService. "
        "If the service is unavailable, a local fallback computation is used."
    ),
    responses={
        200: {"description": "Adjacent roles"},
        404: {"description": "Role not found"},
        503: {"description": "Mapping service unavailable"},
    },
)
def get_role_adjacency(
    role: str = Query(..., description="Role name (or numeric ID as a fallback)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score threshold"),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdjacentRolesResponse:
    """Fetch adjacent roles via mapping service with graceful fallback to local computation."""
    role = (role or "").strip()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role is required")

    try:
        svc_data = mapping_client.get_adjacent_roles(role, limit=limit, min_score=min_score)
        if svc_data is None:
            # Role not found in service; try local resolution for name validation
            return _local_adjacent_roles(db, role, limit=limit, min_score=min_score)
        # Coerce Node JSON into our schema
        return AdjacentRolesResponse.model_validate(svc_data)
    except MappingServiceUnavailable:
        # Fallback to local computation
        return _local_adjacent_roles(db, role, limit=limit, min_score=min_score)


# PUBLIC_INTERFACE
@router.get(
    "/role-adjacency/details",
    response_model=AdjacencyDetailsResponse,
    summary="Get detailed adjacency between two roles",
    description=(
        "Return detailed adjacency (score, shared competencies and deltas) "
        "using the Node RoleMappingService, with a local DB fallback when unavailable."
    ),
    responses={
        200: {"description": "Adjacency details"},
        404: {"description": "Role not found"},
        503: {"description": "Mapping service unavailable"},
    },
)
def get_role_adjacency_details(
    current_role: str = Query(..., description="Current role name"),
    target_role: str = Query(..., description="Target role name"),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdjacencyDetailsResponse:
    """Fetch detailed role adjacency via mapping service with graceful fallback."""
    current_role = (current_role or "").strip()
    target_role = (target_role or "").strip()
    if not current_role or not target_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current_role and target_role are required")

    try:
        svc_data = mapping_client.get_adjacency_details(current_role, target_role)
        if svc_data is None:
            # 404 in service - try local to see if we can compute anyway
            return _local_adjacency_details(db, current_role, target_role)
        return AdjacencyDetailsResponse.model_validate(svc_data)
    except MappingServiceUnavailable:
        return _local_adjacency_details(db, current_role, target_role)
