"""Pydantic schemas for gap analysis and development plans."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.assessment import CompetencyLevel


class GapItem(BaseModel):
    """Computed gap for a single competency."""
    competency_id: int = Field(..., description="Competency identifier")
    competency_name: str = Field(..., description="Competency name")
    current_level: int = Field(..., ge=0, le=5, description="Current user level")
    required_level: int = Field(..., ge=0, le=5, description="Required level for target role")


class GapAnalysisRequest(BaseModel):
    """Request payload to compute gap analysis."""
    target_role_id: int = Field(..., description="Target role identifier")
    current_competencies: List[CompetencyLevel] = Field(..., description="User-reported current competency levels")


class GapAnalysisResult(BaseModel):
    """Result of gap analysis computation."""
    target_role_id: int = Field(..., description="Target role identifier")
    gaps: List[GapItem] = Field(..., description="List of gaps (current < required)")
    total_gaps: int = Field(..., description="Total number of gaps computed")


class PlanStep(BaseModel):
    """A single step in a development plan."""
    description: str = Field(..., description="Step description")
    action_type: str = Field(..., description="Type of action (e.g., Learn, Mentor, Practice)")
    resource: Optional[str] = Field(None, description="Optional resource link or reference")


class DevelopmentPlanCreate(BaseModel):
    """Request to generate a development plan from gap analysis."""
    target_role_id: int = Field(..., description="Target role identifier")
    gaps: List[GapItem] = Field(..., description="Gap items to address")


class DevelopmentPlanRead(BaseModel):
    """Development plan response."""
    id: int = Field(..., description="Plan identifier")
    user_id: int = Field(..., description="Owner user identifier")
    target_role_id: Optional[int] = Field(None, description="Target role identifier")
    steps: List[PlanStep] = Field(..., description="Plan steps")
    created_at: datetime = Field(..., description="Creation timestamp")
    model_config = ConfigDict(from_attributes=True)


class PlanExportRequest(BaseModel):
    """Request to export a development plan."""
    format: str = Field(..., description="Export format", pattern="^(pdf|link)$")
    plan_id: Optional[int] = Field(None, description="Optional plan ID to export (uses latest if omitted)")


class PlanExportResponse(BaseModel):
    """Response for a plan export operation."""
    url: str = Field(..., description="Pre-signed or stub URL where the export is available")
