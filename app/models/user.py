from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.custom_ai import CustomAI
    from app.models.api_key import ApiKey

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuidpk, str100


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuidpk]
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str]
    first_name: Mapped[str100 | None]
    last_name: Mapped[str100 | None]

    custom_ai: Mapped["CustomAI"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=False
    )

    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=False
    )