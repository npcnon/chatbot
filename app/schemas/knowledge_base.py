from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class KnowledgeBaseBase(BaseModel):
    content: str
    source: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    custom_ai_id: UUID


class KnowledgeBaseUpdate(KnowledgeBaseBase):
    content: Optional[str] = None
    source: Optional[str] = None


class KnowledgeBaseInDB(KnowledgeBaseBase):
    id: UUID
    custom_ai_id: UUID
    update_version: int
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseOut(KnowledgeBaseInDB):
    pass