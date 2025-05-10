from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.schemas.personality import PersonalityCreate, PersonalityUpdate, PersonalityOut
from app.services.personality import PersonalityService
from app.services.custom_ai import CustomAIService
from app.services.user import CurrentUserDep, UserService

router = APIRouter(prefix="/personality", tags=["personality"])
#

@router.post("/", response_model=PersonalityOut, status_code=status.HTTP_201_CREATED)
async def create_personality(
    personality_data: PersonalityCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Create a new personality for a custom AI"""
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(personality_data.custom_ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
        
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create a personality for your own custom AI"
        )
    
    # Check if the custom AI already has a personality
    personality_service = PersonalityService(session)
    existing_personality = await personality_service.get_personality_by_ai_id(personality_data.custom_ai_id)
    
    if existing_personality:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom AI already has a personality"
        )
    
    return await personality_service.create_personality(personality_data)

@router.get("/by-user", response_model=PersonalityOut)
async def get_personality_by_user(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get personality for the current user"""
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_user_id(current_user.id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found for this user"
        )
        
    return personality



@router.get("/{personality_id}", response_model=PersonalityOut)
async def get_personality(
    personality_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get a personality by ID"""
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_id(personality_id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(personality.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this personality"
        )
        
    return personality

@router.get("/by-user", response_model=PersonalityOut)
async def get_personality_by_user(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get personality for the current user"""
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_user_id(current_user.id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found for this user"
        )
        
    return personality


@router.get("/by-ai/{ai_id}", response_model=PersonalityOut)
async def get_personality_by_ai(
    ai_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get personality by custom AI ID"""
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
        
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this personality"
        )
    
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_ai_id(ai_id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found"
        )
        
    return personality


@router.put("/{personality_id}", response_model=PersonalityOut)
async def update_personality(
    personality_id: UUID,
    personality_data: PersonalityUpdate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Update a personality"""
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_id(personality_id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(personality.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this personality"
        )
    
    updated_personality = await personality_service.update_personality(personality_id, personality_data)
    return updated_personality


@router.delete("/{personality_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personality(
    personality_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Delete a personality"""
    personality_service = PersonalityService(session)
    personality = await personality_service.get_personality_by_id(personality_id)
    
    if not personality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personality not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(personality.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this personality"
        )
    
    await personality_service.delete_personality(personality_id)