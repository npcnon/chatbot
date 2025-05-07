from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.daos.base import BaseDao
from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseDao(BaseDao):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, knowledge_base_data) -> KnowledgeBase:
        _knowledge_base = KnowledgeBase(**knowledge_base_data)
        self.session.add(_knowledge_base)
        await self.session.commit()
        await self.session.refresh(_knowledge_base)
        return _knowledge_base

    async def get_by_id(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        statement = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        return await self.session.scalar(statement=statement)

    async def get_by_ai_id(self, ai_id) -> list[KnowledgeBase] | None:
        statement = select(KnowledgeBase).where(KnowledgeBase.custom_ai_id == ai_id).order_by(KnowledgeBase.id)
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def get_all(self) -> list[KnowledgeBase]:
        statement = select(KnowledgeBase).order_by(KnowledgeBase.id)
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def delete_all(self) -> None:
        await self.session.execute(delete(KnowledgeBase))
        await self.session.commit()

    async def delete_by_id(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        _knowledge_base = await self.get_by_id(knowledge_base_id=knowledge_base_id)
        if not _knowledge_base:
            return None
        statement = delete(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        await self.session.execute(statement=statement)
        await self.session.commit()
        return _knowledge_base
