"""Pydantic schemas for audit logs."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AuditLogRead(BaseModel):
    """Audit log record returned via admin endpoints."""
    id: int = Field(..., description="Audit log ID")
    user_id: Optional[int] = Field(None, description="User identifier (if available)")
    action: str = Field(..., description="Action performed")
    entity_type: Optional[str] = Field(None, description="Entity type affected")
    entity_id: Optional[str] = Field(None, description="Entity identifier")
    details: Optional[dict] = Field(None, description="Additional details")
    created_at: datetime = Field(..., description="Timestamp")
    model_config = ConfigDict(from_attributes=True)
