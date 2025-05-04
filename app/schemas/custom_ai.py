from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union


class CustomAIBase(BaseModel):
    ai_model: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CustomAICreate(CustomAIBase):
    user_id: UUID


class CustomAIUpdate(CustomAIBase):
    pass


class CustomAIInDB(CustomAIBase):
    id: UUID
    user_id: UUID


class CustomAIOut(CustomAIInDB):
    pass


class CustomAIWithRelations(CustomAIOut):
    # These fields would be populated when needed with related data
    # They're defined as Optional to allow partial population
    knowledge_items: Optional[list] = Field(default_factory=list)
    personality: Optional[dict] = None
    user: Optional[dict] = None