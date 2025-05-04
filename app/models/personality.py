from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.custom_ai import CustomAI


from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.models.base import Base, uuidpk, str100

class Personality(Base):
    __tablename__ = "personality"

    id: Mapped[uuidpk]
    custom_ai_id: Mapped[int] = mapped_column(
        ForeignKey("custom_ai.id"), nullable=False, unique=True 
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    custom_ai: Mapped["CustomAI"] = relationship(back_populates="personality")
