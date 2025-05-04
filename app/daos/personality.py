from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.daos.base import BaseDao
from app.models.personality import Personality


class PersonalityDao(BaseDao):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, personality_data) -> Personality:
        _personality = Personality(**personality_data)
        self.session.add(_personality)
        await self.session.commit()
        await self.session.refresh(_personality)
        return _personality

    async def get_by_id(self, personality_id: UUID) -> Personality | None:
        statement = select(Personality).where(Personality.id == personality_id)
        return await self.session.scalar(statement=statement)

    async def get_by_ai_id(self, ai_id) -> Personality | None:
        statement = select(Personality).where(Personality.custom_ai_id == ai_id)
        return await self.session.scalar(statement=statement)

    async def get_all(self) -> list[Personality]:
        statement = select(Personality).order_by(Personality.id)
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def delete_all(self) -> None:
        await self.session.execute(delete(Personality))
        await self.session.commit()

    async def delete_by_id(self, personality_id: UUID) -> Personality | None:
        _personality = await self.get_by_id(personality_id=personality_id)
        if not _personality:
            return None
        statement = delete(Personality).where(Personality.id == personality_id)
        await self.session.execute(statement=statement)
        await self.session.commit()
        return _personality
