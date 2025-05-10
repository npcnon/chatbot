from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import User
from app.services.api_key import ApiKeyService

# Define API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key_user(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to authenticate a user via API key.
    Returns the user object if authentication succeeds.
    """
    if not api_key:
        return None
        
    api_key_obj = await ApiKeyService.authenticate_api_key(db, api_key)
    
    if not api_key_obj:
        return None
        
    # Return the user associated with this API key
    return api_key_obj.user


async def require_api_key(
    request: Request,
    user: Optional[User] = Depends(get_api_key_user)
) -> User:
    """
    Dependency to require API key authentication.
    Raises 401 Unauthorized if API key is missing or invalid.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return user