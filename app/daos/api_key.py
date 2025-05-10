from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.daos.base import BaseDao
from app.models.api_key import ApiKey


class ApiKeyDao(BaseDao):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, api_key_data) -> ApiKey:
        _api_key = ApiKey(**api_key_data)
        self.session.add(_api_key)
        await self.session.commit()
        await self.session.refresh(_api_key)
        return _api_key

    async def get_by_id(self, api_key_id: UUID) -> ApiKey | None:
        statement = select(ApiKey).where(ApiKey.id == api_key_id)
        return await self.session.scalar(statement=statement)

    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        """Get an API key by its hashed value"""
        statement = select(ApiKey).where(ApiKey.key_hash == key_hash)
        return await self.session.scalar(statement=statement)

    async def get_by_user_id(self, user_id: UUID) -> list[ApiKey]:
        """Get all API keys for a specific user"""
        statement = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def get_all(self) -> list[ApiKey]:
        statement = select(ApiKey).order_by(ApiKey.id)
        result = await self.session.execute(statement=statement)
        return result.scalars().all()

    async def update_usage(self, api_key_id: UUID) -> ApiKey | None:
        """Update the usage count and last_used_at timestamp for an API key"""
        from datetime import datetime, timezone
        
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            return None
            
        api_key.usage_count += 1
        api_key.last_used_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def delete_all(self) -> None:
        statement = delete(ApiKey)
        await self.session.execute(statement)
        await self.session.commit()

    async def delete_by_id(self, api_key_id: UUID) -> ApiKey | None:
        _api_key = await self.get_by_id(api_key_id=api_key_id)
        if not _api_key:
            return None
            
        await self.session.delete(_api_key)
        await self.session.commit()
        return _api_key