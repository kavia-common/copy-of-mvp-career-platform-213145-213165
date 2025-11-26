"""Pydantic schemas for Role entity."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class RoleBase(BaseModel):
    """Shared fields across role payloads."""
    name: str = Field(..., description="Human-readable name of the role (unique).")
    description: Optional[str] = Field(
        None, description="Optional description of the role."
    )


class RoleCreate(RoleBase):
    """Payload for creating a new role."""
    pass


class RoleRead(BaseModel):
    """Response schema for Role."""

    id: int = Field(..., description="Unique ID of the role.")
    name: str = Field(..., description="Name of the role.")
    description: Optional[str] = Field(None, description="Description of the role.")
    created_at: datetime = Field(..., description="Creation timestamp.")

    # Enable reading from ORM objects
    model_config = ConfigDict(from_attributes=True)
