from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.daos.custom_ai import CustomAIDao
from app.daos.personality import PersonalityDao
from app.daos.knowledge_base import KnowledgeBaseDao
from app.models.custom_ai import CustomAI
from app.schemas.custom_ai import CustomAICreate, CustomAIUpdate, CustomAIWithRelations


class CustomAIService:
    
    def __init__(self, session: AsyncSession):
        self.custom_ai_dao = CustomAIDao(session)
        self.personality_dao = PersonalityDao(session)  # Assuming you have this DAO
        self.knowledge_base_dao = KnowledgeBaseDao(session)  # Assuming you have this DAO
        self.session = session




    async def create_custom_ai(self, custom_ai_data: CustomAICreate) -> CustomAI:
        """Create a new custom AI"""
        custom_ai_dict = custom_ai_data.model_dump()
        return await self.custom_ai_dao.create(custom_ai_dict)

    async def get_custom_ai_by_id(self, custom_ai_id: UUID) -> CustomAI | None:
        """Get a custom AI by ID"""
        return await self.custom_ai_dao.get_by_id(custom_ai_id)

    async def get_custom_ai_by_user_id(self, user_id: UUID) -> CustomAI | None:
        """Get a custom AI by user ID"""
        # This is not in the DAO, so we'll need to add the method
        # For now, we'll use the existing methods
        custom_ais = await self.custom_ai_dao.get_all()
        for ai in custom_ais:
            if ai.user_id == user_id:
                return ai
        return None

    async def update_custom_ai(self, custom_ai_id: UUID, custom_ai_data: CustomAIUpdate) -> CustomAI | None:
        """Update a custom AI"""
        custom_ai = await self.get_custom_ai_by_id(custom_ai_id)
        if not custom_ai:
            return None
            
        # Update only the provided fields
        update_data = custom_ai_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(custom_ai, key, value)
            
        self.session.add(custom_ai)
        await self.session.commit()
        await self.session.refresh(custom_ai)
        return custom_ai

    async def delete_custom_ai(self, custom_ai_id: UUID) -> CustomAI | None:
        """Delete a custom AI"""
        return await self.custom_ai_dao.delete_by_id(custom_ai_id)

    async def get_all_custom_ais(self) -> list[CustomAI]:
        """Get all custom AIs"""
        return await self.custom_ai_dao.get_all()

    async def get_custom_ai_with_relations(self, custom_ai_id: UUID) -> CustomAIWithRelations | None:
        """Get a custom AI with its related knowledge items, personality, and user"""
        custom_ai = await self.get_custom_ai_by_id(custom_ai_id)
        if not custom_ai:
            return None
            
        # Convert to Pydantic model
        custom_ai_dict = CustomAIWithRelations.model_validate(custom_ai).model_dump()
        
        # Populate related data if available
        if custom_ai.knowledge_items:
            custom_ai_dict["knowledge_items"] = [item.model_dump() for item in custom_ai.knowledge_items]
        
        if custom_ai.personality:
            custom_ai_dict["personality"] = custom_ai.personality.model_dump()
        
        if custom_ai.user:
            user_dict = custom_ai.user.model_dump(exclude={"password"})
            custom_ai_dict["user"] = user_dict
        
        return CustomAIWithRelations.model_validate(custom_ai_dict)