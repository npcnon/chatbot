from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.daos.base import BaseDao
from app.models.custom_ai import CustomAI
from app.models.personality import Personality
class CustomAIDao(BaseDao):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, custom_ai_data) -> CustomAI:
        _custom_ai = CustomAI(**custom_ai_data)
        self.session.add(_custom_ai)
        await self.session.commit()
        await self.session.refresh(_custom_ai)
        return _custom_ai

    async def get_by_id(self, custom_ai_id: UUID) -> CustomAI | None:
        statement = select(CustomAI).where(CustomAI.id == custom_ai_id)
        return await self.session.scalar(statement=statement)

    async def get_by_personality_id(self, personality_id) -> CustomAI | None:
        statement = (
            select(CustomAI)
            .join(CustomAI.personality)
            .where(Personality.id == personality_id)
        )
        return await self.session.scalar(statement=statement)

    async def get_all(self) -> list[CustomAI]:
        statement = select(CustomAI).order_by(CustomAI.id)
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def delete_all(self) -> None:
        await self.session.execute(delete(CustomAI))
        await self.session.commit()

    async def delete_by_id(self, custom_ai_id: UUID) -> CustomAI | None:
        _custom_ai = await self.get_by_id(custom_ai_id=custom_ai_id)
        if not _custom_ai:
            return None
        statement = delete(CustomAI).where(CustomAI.id == custom_ai_id)
        await self.session.execute(statement=statement)
        await self.session.commit()
        return _custom_ai
