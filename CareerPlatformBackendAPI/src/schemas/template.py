"""Pydantic schemas for Template entity."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TemplateBase(BaseModel):
    """Shared fields for Template payloads."""

    name: str = Field(..., description="Human-readable name of the template.")
    content: Optional[str] = Field(
        None,
        description="Template content, e.g., text/JSON describing plan structure.",
    )


class TemplateCreate(TemplateBase):
    """Payload for creating a new template."""
    pass


class TemplateUpdate(BaseModel):
    """Payload for updating an existing template."""

    name: Optional[str] = Field(None, description="New name for the template.")
    content: Optional[str] = Field(
        None, description="Updated content for the template."
    )


class TemplateOut(BaseModel):
    """Response schema for Template."""

    id: int = Field(..., description="Unique ID of the template.")
    name: str = Field(..., description="Name of the template.")
    content: Optional[str] = Field(None, description="Content of the template.")
    created_at: datetime = Field(..., description="Creation timestamp.")

    # Enable reading from ORM objects
    model_config = ConfigDict(from_attributes=True)
