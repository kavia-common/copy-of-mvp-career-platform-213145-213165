"""SQLAlchemy model for Competency entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class Competency(Base):
    """Competency definition with optional description/definition."""

    __tablename__ = "competencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role_mappings = relationship("RoleCompetency", back_populates="competency", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"Competency(id={self.id!r}, name={self.name!r})"
