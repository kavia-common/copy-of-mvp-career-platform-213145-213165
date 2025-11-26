"""Pydantic schemas for User entity."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class UserOut(BaseModel):
    """Public user information returned by the API."""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="Full name")
    is_admin: bool = Field(..., description="Is user an administrator?")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    """Payload to update basic user profile properties."""
    full_name: Optional[str] = Field(None, description="Updated full name")
