"""Pydantic schemas for Role Mapping and Adjacency endpoints."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class AdjacentRoleItem(BaseModel):
    """Suggested adjacent role with similarity score and quick stats."""
    role: str = Field(..., description="Role name")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0..1)")
    sharedCompetencies: int = Field(..., description="Count of shared competencies")
    missingInCurrent: int = Field(..., description="Competencies present in target but missing in current")
    extraInCurrent: int = Field(..., description="Competencies present in current but not in target")


class AdjacentRolesResponse(BaseModel):
    """Response for adjacent roles request."""
    role: str = Field(..., description="Requested role")
    total: int = Field(..., description="Total items in response (after filtering)")
    items: List[AdjacentRoleItem] = Field(..., description="Adjacent role suggestions")


class AdjacencySharedCompetency(BaseModel):
    """Shared competency with level deltas."""
    competency: str = Field(..., description="Competency name")
    current_level: int = Field(..., description="Current required level for current role")
    target_level: int = Field(..., description="Required level for target role")
    delta: int = Field(..., description="target_level - current_level")


class AdjacencyMissing(BaseModel):
    """Competency required in target but missing in current."""
    competency: str = Field(..., description="Competency name")
    target_level: int = Field(..., description="Required level for target role")


class AdjacencyExtra(BaseModel):
    """Competency required in current but not required in target."""
    competency: str = Field(..., description="Competency name")
    current_level: int = Field(..., description="Required level for current role")


class AdjacencyStats(BaseModel):
    """Aggregate stats for adjacency details."""
    sharedCompetencies: int = Field(..., description="Number of shared competencies")
    missingInCurrent: int = Field(..., description="Count missing in current role")
    extraInCurrent: int = Field(..., description="Count extra in current role")


class AdjacencyDetailsResponse(BaseModel):
    """Detailed adjacency comparison for two roles."""
    currentRole: str = Field(..., description="Current role name")
    targetRole: str = Field(..., description="Target role name")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0..1)")
    shared: List[AdjacencySharedCompetency] = Field(..., description="Shared competencies with deltas")
    missingInCurrent: List[AdjacencyMissing] = Field(..., description="Competencies missing in current role")
    extraInCurrent: List[AdjacencyExtra] = Field(..., description="Competencies extra in current role")
    stats: AdjacencyStats = Field(..., description="Aggregated counts")

    model_config = ConfigDict(from_attributes=True)
