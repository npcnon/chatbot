from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Union
from uuid import UUID
from pydantic import BaseModel

from app.db import get_session
from app.daos.custom_ai import CustomAIDao
from app.daos.personality import PersonalityDao
from app.daos.knowledge_base import KnowledgeBaseDao
from app.daos.api_key import ApiKeyDao
from app.services.api_key import ApiKeyService
from app.services.ai_service import HuggingFaceService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

class ChatRequest(BaseModel):
    ai_id: UUID
    user_text: str
    chat_history: Optional[List[Dict[str, str]]] = None

class ApiKeyChatRequest(BaseModel):
    user_text: str
    chat_history: Optional[List[Dict[str, str]]] = None
    model_override: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    chat_history: List[Dict[str, str]]

async def get_huggingface_service(db: AsyncSession = Depends(get_session)) -> HuggingFaceService:
    custom_ai_dao = CustomAIDao(db)
    personality_dao = PersonalityDao(db)
    knowledge_base_dao = KnowledgeBaseDao(db)
    api_key_dao = ApiKeyDao(db)
    api_key_service = ApiKeyService(api_key_dao)
    return HuggingFaceService(
        custom_ai_dao, 
        personality_dao, 
        knowledge_base_dao,
        api_key_dao,
        api_key_service
    )

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    hf_service: HuggingFaceService = Depends(get_huggingface_service),
):
    """
    Chat with a custom AI using HuggingFace model.
    The system message will be taken from the AI's personality,
    and context will be taken from the AI's knowledge base.
    """
    try:
        response, chat_history = await hf_service.chat(
            ai_id=request.ai_id,
            user_text=request.user_text,
            chat_history=request.chat_history
        )
        
        return ChatResponse(
            response=response,
            chat_history=chat_history
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/api", response_model=ChatResponse)
async def chat_with_api_key(
    request: ApiKeyChatRequest,
    api_key: str = Header(...),
    hf_service: HuggingFaceService = Depends(get_huggingface_service),
):
    """
    Chat with a custom AI using an API key for authentication.
    The system message and knowledge context are determined by the user associated with the API key.
    
    Requires an API key to be provided in the header as 'api_key'.
    """
    try:
        response, chat_history = await hf_service.chat_with_api_key(
            api_key=api_key,
            user_text=request.user_text,
            chat_history=request.chat_history,
            model_override=request.model_override
        )
        
        return ChatResponse(
            response=response,
            chat_history=chat_history
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")