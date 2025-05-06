from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.schemas.custom_ai import CustomAICreate, CustomAIUpdate, CustomAIOut, CustomAIWithRelations
from app.services.custom_ai import CustomAIService
from app.services.user import UserService

router = APIRouter(prefix="/custom-ai", tags=["custom-ai"])


@router.post("/", response_model=CustomAIOut, status_code=status.HTTP_201_CREATED)
async def create_custom_ai(
    custom_ai_data: CustomAICreate,
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new custom AI for the current user"""
    if str(custom_ai_data.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create a custom AI for your own account"
        )
        
    custom_ai_service = CustomAIService(session)
    
    # Check if user already has a custom AI
    existing_ai = await custom_ai_service.get_custom_ai_by_user_id(current_user.id)
    if existing_ai:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a custom AI"
        )
    
    return await custom_ai_service.create_custom_ai(custom_ai_data)


@router.get("/me", response_model=CustomAIOut)
async def get_my_custom_ai(
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the current user's custom AI"""
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_user_id(current_user.id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
        
    return custom_ai


@router.get("/me/with-relations", response_model=CustomAIWithRelations)
async def get_my_custom_ai_with_relations(
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the current user's custom AI with related data"""
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_user_id(current_user.id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
        
    return await custom_ai_service.get_custom_ai_with_relations(custom_ai.id)


@router.get("/{custom_ai_id}", response_model=CustomAIOut)
async def get_custom_ai(
    custom_ai_id: UUID,
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a custom AI by ID"""
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(custom_ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
    
    # Only allow access to the user's own custom AI
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this custom AI"
        )
        
    return custom_ai


@router.put("/{custom_ai_id}", response_model=CustomAIOut)
async def update_custom_ai(
    custom_ai_id: UUID,
    custom_ai_data: CustomAIUpdate,
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a custom AI"""
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(custom_ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
    
    # Only allow the user to update their own custom AI
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this custom AI"
        )
    
    updated_ai = await custom_ai_service.update_custom_ai(custom_ai_id, custom_ai_data)
    return updated_ai


@router.delete("/{custom_ai_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_ai(
    custom_ai_id: UUID,
    current_user: User = Depends(UserService.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a custom AI"""
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(custom_ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
    
    # Only allow the user to delete their own custom AI
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this custom AI"
        )
    
    await custom_ai_service.delete_custom_ai(custom_ai_id)