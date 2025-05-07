from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.custom_ai import CustomAI


from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.models.base import Base, uuidpk,uuidfk

class Personality(Base):
    __tablename__ = "personality"

    id: Mapped[uuidpk]
    custom_ai_id: Mapped[uuidfk] = mapped_column(
        ForeignKey("custom_ai.id", ondelete='CASCADE'), nullable=False, unique=True 
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    custom_ai: Mapped["CustomAI"] = relationship(
        back_populates="personality",
        single_parent=True
    )
