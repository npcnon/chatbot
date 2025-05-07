from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.daos.personality import PersonalityDao
from app.models.personality import Personality
from app.schemas.personality import PersonalityCreate, PersonalityUpdate


class PersonalityService:
    
    def __init__(self, session: AsyncSession):
        self.personality_dao = PersonalityDao(session)
        self.session = session

    async def create_personality(self, personality_data: PersonalityCreate) -> Personality:
        """Create a new personality"""
        personality_dict = personality_data.model_dump()
        return await self.personality_dao.create(personality_dict)

    async def get_personality_by_id(self, personality_id: UUID) -> Personality | None:
        """Get a personality by ID"""
        return await self.personality_dao.get_by_id(personality_id)

    async def get_personality_by_ai_id(self, ai_id: UUID) -> Personality | None:
        """Get a personality by custom AI ID"""
        return await self.personality_dao.get_by_ai_id(ai_id)

    async def update_personality(self, personality_id: UUID, personality_data: PersonalityUpdate) -> Personality | None:
        """Update a personality"""
        personality = await self.get_personality_by_id(personality_id)
        if not personality:
            return None
            
        # Update only the provided fields
        update_data = personality_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(personality, key, value)
            
        self.session.add(personality)
        await self.session.commit()
        await self.session.refresh(personality)
        return personality

    async def delete_personality(self, personality_id: UUID) -> Personality | None:
        """Delete a personality"""
        return await self.personality_dao.delete_by_id(personality_id)

    async def get_all_personalities(self) -> list[Personality]:
        """Get all personalities"""
        return await self.personality_dao.get_all()