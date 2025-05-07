from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.custom_ai import CustomAI


from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, uuidpk, uuidfk
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuidpk]
    custom_ai_id: Mapped[uuidfk] = mapped_column(ForeignKey("custom_ai.id", ondelete='CASCADE'), nullable=False)
    update_version: Mapped[int] = mapped_column(default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )
    custom_ai: Mapped["CustomAI"] = relationship(back_populates="knowledge_items")