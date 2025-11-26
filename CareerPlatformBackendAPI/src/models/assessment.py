"""SQLAlchemy model for user competency assessments."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Assessment(Base):
    """Stores a user's self-reported competency levels, optionally for a target role."""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    target_role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True)
    competency_levels: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {competency_id: level}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="assessments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Assessment(id={self.id!r}, user_id={self.user_id!r}, target_role_id={self.target_role_id!r})"
