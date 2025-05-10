from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ApiKeyBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreate(ApiKeyBase):
    expires_in_days: Optional[int] = None


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ApiKeyInDB(ApiKeyBase):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int


class ApiKeyOut(ApiKeyInDB):
    pass


class ApiKeyWithSecret(ApiKeyOut):
    key: str = Field(..., description="The raw API key (only shown once)")