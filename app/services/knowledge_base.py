from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.daos.knowledge_base import KnowledgeBaseDao
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate


class KnowledgeBaseService:
    
    def __init__(self, session: AsyncSession):
        self.knowledge_base_dao = KnowledgeBaseDao(session)
        self.session = session

    async def create_knowledge_base(self, knowledge_base_data: KnowledgeBaseCreate) -> KnowledgeBase:
        """Create a new knowledge base"""
        knowledge_base_dict = knowledge_base_data.model_dump()
        return await self.knowledge_base_dao.create(knowledge_base_dict)

    async def get_knowledge_base_by_id(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        """Get a knowledge base by ID"""
        return await self.knowledge_base_dao.get_by_id(knowledge_base_id)

    async def get_knowledge_base_by_ai_id(self, ai_id: UUID) -> KnowledgeBase | None:
        """Get a knowledge base by custom AI ID"""
        return await self.knowledge_base_dao.get_by_ai_id(ai_id)

    async def update_knowledge_base(self, knowledge_base_id: UUID, knowledge_base_data: KnowledgeBaseUpdate) -> KnowledgeBase | None:
        """Update a knowledge base"""
        knowledge_base = await self.get_knowledge_base_by_id(knowledge_base_id)
        if not knowledge_base:
            return None
            
        # Update only the provided fields
        update_data = knowledge_base_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(knowledge_base, key, value)
        
        # Increment update_version
        knowledge_base.update_version += 1
            
        self.session.add(knowledge_base)
        await self.session.commit()
        await self.session.refresh(knowledge_base)
        return knowledge_base

    async def delete_knowledge_base(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        """Delete a knowledge base"""
        return await self.knowledge_base_dao.delete_by_id(knowledge_base_id)

    async def get_all_knowledge_bases(self) -> list[KnowledgeBase]:
        """Get all knowledge bases"""
        return await self.knowledge_base_dao.get_all()