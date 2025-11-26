"""SQLAlchemy model for mapping required competency levels per Role."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class RoleCompetency(Base):
    """Mapping between Roles and Competencies with required proficiency level."""

    __tablename__ = "role_competencies"
    __table_args__ = (UniqueConstraint("role_id", "competency_id", name="uq_role_competency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id", ondelete="CASCADE"), index=True, nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # Range e.g., 0..5

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role = relationship("Role")
    competency = relationship("Competency", back_populates="role_mappings")

    def __repr__(self) -> str:  # pragma: no cover
        return f"RoleCompetency(role_id={self.role_id!r}, competency_id={self.competency_id!r}, required_level={self.required_level!r})"
