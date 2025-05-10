from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.user import User

import datetime
import secrets
import uuid
from sqlalchemy import ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, uuidpk, uuidfk, str100


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[uuidpk]
    user_id: Mapped[uuidfk] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    
    # The actual API key (hashed in the database)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # API key metadata
    name: Mapped[str100] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Permissions and status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Rate limiting (optional)
    rate_limit: Mapped[int | None] = mapped_column(nullable=True)  # Requests per hour
    
    # Usage tracking
    last_used_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")
    
    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired