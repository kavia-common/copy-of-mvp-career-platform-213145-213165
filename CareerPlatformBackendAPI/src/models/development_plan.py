"""SQLAlchemy model for development plans generated from gap analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class DevelopmentPlan(Base):
    """Stores a user's generated development plan for a target role."""

    __tablename__ = "development_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    target_role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # list of step objects
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="development_plans")

    def __repr__(self) -> str:  # pragma: no cover
        return f"DevelopmentPlan(id={self.id!r}, user_id={self.user_id!r}, target_role_id={self.target_role_id!r})"
