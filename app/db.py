# app/db.py
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import settings

# Convert PostgreSQL URL to async version (add +asyncpg)
postgres_url = settings.POSTGRES_URL
if postgres_url.startswith("postgresql://"):
    postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine and session
engine = create_async_engine(postgres_url, echo=True)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # This will only execute after the request is complete
            # Commit any pending changes if no exception occurred
            await session.commit()
        except Exception:
            # Rollback in case of exception
            await session.rollback()
            raise
        # The session.close() is handled by the context manager (async with)

SessionDep = Annotated[AsyncSession, Depends(get_session)]