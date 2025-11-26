"""Pydantic schemas for Competency and Role-Competency mappings."""
from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class CompetencyRead(BaseModel):
    """Response schema for a Competency."""
    id: int = Field(..., description="Competency ID")
    name: str = Field(..., description="Competency name")
    definition: Optional[str] = Field(None, description="Definition/description of the competency")
    category: Optional[str] = Field(None, description="Optional category")
    model_config = ConfigDict(from_attributes=True)


class CompetencyWithRequirement(CompetencyRead):
    """Competency plus required level for a role."""
    required_level: int = Field(..., description="Required level for the competency in the role context (0..5)")
