"""SQLAlchemy model definition for the Role entity."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class Role(Base):
    """Role entity representing a job/position within the platform."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, unique=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - representation only
        return f"Role(id={self.id!r}, name={self.name!r})"
