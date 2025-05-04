from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.personality import Personality
    from app.models.user import User

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from app.models.base import Base, uuidpk,uuidfk


class CustomAI(Base):
    __tablename__ = "custom_ai"

    id: Mapped[uuidpk]
    user_id: Mapped[uuidfk] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)

    ai_model: Mapped[str] = mapped_column(
        String(255), 
        default="mistralai/Mistral-7B-Instruct-v0.3",
        server_default="mistralai/Mistral-7B-Instruct-v0.3"
    )    
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
    
    user: Mapped["User"] = relationship(
        back_populates="custom_ai",
        single_parent=True    
    )