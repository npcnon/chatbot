from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.utils import UtilsService


class UserDAO:
    async def get(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, user_create: UserCreate) -> User:
        hashed_password = UtilsService.get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            password=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name
        )
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            raise ValueError("Email already registered")

    async def update(self, db: AsyncSession, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        db_user = await self.get(db, user_id)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["password"] = UtilsService.get_password_hash(update_data["password"])

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def delete(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        db_user = await self.get(db, user_id)
        if not db_user:
            return None
        
        await db.delete(db_user)
        await db.commit()
        return db_user