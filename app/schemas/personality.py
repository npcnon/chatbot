from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class PersonalityBase(BaseModel):
    content: str
    source: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PersonalityCreate(PersonalityBase):
    custom_ai_id: UUID


class PersonalityUpdate(PersonalityBase):
    content: Optional[str] = None
    source: Optional[str] = None


class PersonalityInDB(PersonalityBase):
    id: UUID
    custom_ai_id: UUID
    created_at: datetime
    updated_at: datetime


class PersonalityOut(PersonalityInDB):
    pass