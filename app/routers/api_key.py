from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db import get_session
from app.daos.api_key import ApiKeyDao
from app.services.api_key import ApiKeyService
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut, ApiKeyWithSecret
from app.services.user import CurrentUserDep

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
)


async def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    api_key_dao = ApiKeyDao(session)
    return ApiKeyService(api_key_dao)


@router.post("", response_model=ApiKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: CurrentUserDep,
    api_key_service: ApiKeyService = Depends(get_api_key_service),
):
    """Create a new API key for the current user"""
    try:
        # Create a new API key
        raw_key, api_key = await api_key_service.create_api_key(
            user_id=current_user.id,
            name=api_key_data.name,
            description=api_key_data.description,
            expires_in_days=api_key_data.expires_in_days
        )
        
        # Return both the API key object and the raw key
        api_key_dict = ApiKeyOut.model_validate(api_key).model_dump()
        return {**api_key_dict, "key": raw_key}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[ApiKeyOut])
async def list_api_keys(
    current_user: CurrentUserDep,
    api_key_service: ApiKeyService = Depends(get_api_key_service),
):
    """List all API keys for the current user"""
    return await api_key_service.get_user_api_keys(current_user.id)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    current_user: CurrentUserDep,
    api_key_service: ApiKeyService = Depends(get_api_key_service),
):
    """Delete an API key"""
    # First check that this API key belongs to the current user
    api_keys = await api_key_service.get_user_api_keys(current_user.id)
    if not any(str(api_key.id) == str(api_key_id) for api_key in api_keys):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key"
        )
    
    success = await api_key_service.delete_api_key(api_key_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.post("/{api_key_id}/revoke", response_model=ApiKeyOut)
async def revoke_api_key(
    api_key_id: UUID,
    current_user: CurrentUserDep,
    api_key_service: ApiKeyService = Depends(get_api_key_service),
    session: AsyncSession = Depends(get_session),
):
    """Revoke an API key (mark as inactive)"""
    # First check that this API key belongs to the current user
    api_keys = await api_key_service.get_user_api_keys(current_user.id)
    if not any(str(api_key.id) == str(api_key_id) for api_key in api_keys):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this API key"
        )
    
    success = await api_key_service.revoke_api_key(api_key_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    
    # Get the updated API key
    api_key_dao = ApiKeyDao(session)
    updated_key = await api_key_dao.get_by_id(api_key_id)
    return updated_key