from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseOut
from app.services.knowledge_base import KnowledgeBaseService
from app.services.custom_ai import CustomAIService
from app.services.user import UserService
from app.services.user import CurrentUserDep
router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.post("/", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    knowledge_base_data: KnowledgeBaseCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Create a new knowledge base item"""
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(knowledge_base_data.custom_ai_id)
    
    if not custom_ai:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom AI not found"
        )
        
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create knowledge base items for your own custom AI"
        )
    
    knowledge_base_service = KnowledgeBaseService(session)
    return await knowledge_base_service.create_knowledge_base(knowledge_base_data)

@router.get("/by-user", response_model=list[KnowledgeBaseOut])
async def get_knowledge_bases_by_user(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get all knowledge base items for the current user"""
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_bases = await knowledge_base_service.get_knowledge_bases_by_user_id(current_user.id)
    return knowledge_bases

@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get a knowledge base item by ID"""
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_base = await knowledge_base_service.get_knowledge_base_by_id(knowledge_base_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base item not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(knowledge_base.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this knowledge base item"
        )
        
    return knowledge_base


@router.get("/by-ai/{ai_id}", response_model=list[KnowledgeBaseOut])
async def get_knowledge_base_by_ai(
    ai_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get knowledge base item by custom AI ID"""
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
            detail="You don't have permission to access this knowledge base item"
        )
    
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_base = await knowledge_base_service.get_knowledge_base_by_ai_id(ai_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base item not found"
        )
        
    return knowledge_base

@router.get("/by-user", response_model=list[KnowledgeBaseOut])
async def get_knowledge_bases_by_user(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Get all knowledge base items for the current user"""
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_bases = await knowledge_base_service.get_knowledge_bases_by_user_id(current_user.id)
    return knowledge_bases




@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    knowledge_base_data: KnowledgeBaseUpdate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Update a knowledge base item"""
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_base = await knowledge_base_service.get_knowledge_base_by_id(knowledge_base_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base item not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(knowledge_base.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this knowledge base item"
        )
    
    updated_knowledge_base = await knowledge_base_service.update_knowledge_base(knowledge_base_id, knowledge_base_data)
    return updated_knowledge_base


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):
    """Delete a knowledge base item"""
    knowledge_base_service = KnowledgeBaseService(session)
    knowledge_base = await knowledge_base_service.get_knowledge_base_by_id(knowledge_base_id)
    
    if not knowledge_base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base item not found"
        )
    
    # Verify the custom AI belongs to the current user
    custom_ai_service = CustomAIService(session)
    custom_ai = await custom_ai_service.get_custom_ai_by_id(knowledge_base.custom_ai_id)
    
    if str(custom_ai.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this knowledge base item"
        )
    
    await knowledge_base_service.delete_knowledge_base(knowledge_base_id)