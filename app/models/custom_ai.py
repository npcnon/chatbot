from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.personality import Personality

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base, intpk


class CustomAI(Base):
    __tablename__ = "custom_ai"

    id: Mapped[intpk]
    model: Mapped[str | None] = mapped_column(String(255))
    
    knowledge_items: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="custom_ai",
        cascade="all, delete-orphan",
        passive_deletes=False
    )

    personality: Mapped["Personality"] = relationship(
        back_populates="custom_ai",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=False
    )