"""Pydantic schemas for assessments."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class CompetencyLevel(BaseModel):
    """Pair of competency ID and user-reported level (0..5)."""
    competency_id: int = Field(..., description="Competency identifier")
    level: int = Field(..., ge=0, le=5, description="Self-assessed level (0..5)")


class AssessmentCreate(BaseModel):
    """Payload to submit a user assessment."""
    target_role_id: Optional[int] = Field(None, description="Target role to compare against")
    competencies: List[CompetencyLevel] = Field(..., description="List of competency levels")


class AssessmentRead(BaseModel):
    """Response for an assessment submission."""
    id: int = Field(..., description="Assessment identifier")
    user_id: int = Field(..., description="User identifier")
    target_role_id: Optional[int] = Field(None, description="Target role identifier")
    competency_levels: Dict[str, int] = Field(..., description="Mapping of competency_id to level")
    created_at: datetime = Field(..., description="Creation timestamp")
    model_config = ConfigDict(from_attributes=True)
