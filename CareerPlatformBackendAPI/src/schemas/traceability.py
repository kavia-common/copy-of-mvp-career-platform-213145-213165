"""Pydantic schemas for traceability."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class TraceabilityRead(BaseModel):
    """Traceability mapping for an entity."""
    id: int = Field(..., description="Identifier")
    entity_type: str = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    source_documents: List[str] = Field(..., description="Related source documents")
    model_config = ConfigDict(from_attributes=True)
