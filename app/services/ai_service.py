from typing import List, Dict, Optional, Tuple
import os
from uuid import UUID
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import traceback
from openai import OpenAI
from app.daos.custom_ai import CustomAIDao
from app.daos.personality import PersonalityDao
from app.daos.knowledge_base import KnowledgeBaseDao
from app.daos.api_key import ApiKeyDao
from app.services.api_key import ApiKeyService
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
class HuggingFaceService:
    """Service for interacting with HuggingFace models"""
    
    def __init__(self, 
                 custom_ai_dao: CustomAIDao, 
                 personality_dao: PersonalityDao,
                 knowledge_base_dao: KnowledgeBaseDao,
                 api_key_dao: ApiKeyDao = None,
                 api_key_service: ApiKeyService = None):
        self.custom_ai_dao = custom_ai_dao
        self.personality_dao = personality_dao
        self.knowledge_base_dao = knowledge_base_dao
        self.api_key_dao = api_key_dao
        self.api_key_service = api_key_service
        self.hf_token = os.getenv("HF_TOKEN")
        self.kluster_key = os.getenv("KLUSTER_KEY")
    def get_inference_client(self, model_id: str):
        """Get a HuggingFace InferenceClient instance"""
        return InferenceClient(
            model=model_id,
            token=self.hf_token
        )
        
    async def chat(self, 
                 ai_id: UUID, 
                 user_text: str,
                 chat_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, List[Dict[str, str]]]:
        """
        Generate a chat response based on the custom AI configuration.
        
        Args:
            ai_id: UUID of the custom AI
            user_text: Text input from the user
            chat_history: Optional chat history
            
        Returns:
            Tuple of (response, updated_chat_history)
        """
        if chat_history is None:
            chat_history = []
            
        try:
            # Get the custom AI details
            custom_ai = await self.custom_ai_dao.get_by_id(ai_id)
            if not custom_ai:
                raise ValueError(f"No CustomAI found with id {ai_id}")
            
            # Get the personality (system message)
            personality = await self.personality_dao.get_by_ai_id(ai_id)
            system_message = personality.content if personality else "You are a helpful AI assistant."
            
            # Get knowledge base items
            knowledge_items = await self.knowledge_base_dao.get_by_ai_id(ai_id)
            knowledge_context = "\n\n".join([item.content for item in knowledge_items]) if knowledge_items else ""
            
            # Log the model being used
            print(f"Using model: {custom_ai.ai_model}")
            
            try:
                # Get the inference client
                client = OpenAI(
                    api_key=self.kluster_key, 
                    base_url="https://api.kluster.ai/v1"
                )

                # Build the conversation
                messages = [
                    {"role": "system", "content": system_message},
                ]

                if knowledge_context:
                    messages.append({"role": "system", "content": knowledge_context})

                # Add chat history
                if chat_history:
                    messages.extend(chat_history)  # Add the chat history objects directly

                # Add user prompt
                messages.append({"role": "user", "content": user_text})

                # Call the chat completion endpoint
                response_obj = client.chat.completions.create(
                    model=custom_ai.ai_model,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=512,
                )

                # Extract the response
                response = response_obj.choices[0].message.content.strip()

                # Clean up response
                if "AI:" in response:
                    response = response.split("AI:")[-1].strip()
                    
                # Update chat history
                chat_history.append({"role": "user", "content": user_text})
                chat_history.append({"role": "assistant", "content": response})
                
                return response, chat_history
                
            except Exception as e:
                print(f"Error in AI API call: {str(e)}")
                print(traceback.format_exc())
                
                # Provide a fallback response
                fallback_response = "I'm sorry, I encountered an error while processing your request. Please try again later."
                chat_history.append({"role": "user", "content": user_text})
                chat_history.append({"role": "assistant", "content": fallback_response})
                return fallback_response, chat_history
                
        except Exception as e:
            print(f"Error in chat method: {str(e)}")
            print(traceback.format_exc())
            raise
            

    async def chat_with_api_key(self, 
                              api_key: str, 
                              user_text: str,
                              chat_history: Optional[List[Dict[str, str]]] = None,
                              model_override: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
        """
        Generate a chat response using an API key for authentication.
        
        Args:
            api_key: API key for authentication
            user_text: Text input from the user
            chat_history: Optional chat history
            model_override: Optional model override
            
        Returns:
            Tuple of (response, updated_chat_history)
        """
        if not self.api_key_service:
            raise ValueError("API key service not initialized")
            
        # Validate the API key
        api_key_record = await self.api_key_service.validate_api_key(api_key)
        if not api_key_record:
            raise ValueError("Invalid API key")
            
        # Get the user associated with the API key
        user_id = api_key_record.user_id
        
        # Get the custom AI for this user
        custom_ais = await self.custom_ai_dao.get_by_user_id(user_id)
        if not custom_ais or len(custom_ais) == 0:
            raise ValueError("No custom AI found for this user")
            
        # Use the first custom AI (assuming one per user)
        custom_ai = custom_ais[0]
        
        # Get the personality
        personality = await self.personality_dao.get_by_ai_id(custom_ai.id)
        system_message = personality.content if personality else "You are a helpful AI assistant."
        
        # Get knowledge base items
        knowledge_items = await self.knowledge_base_dao.get_by_ai_id(custom_ai.id)
        knowledge_context = "\n\n".join([item.content for item in knowledge_items]) if knowledge_items else ""
        
        # Initialize chat history if not provided
        if chat_history is None:
            chat_history = []
        
        # Determine which model to use (override or the one configured for the AI)
        model_id = model_override if model_override else custom_ai.ai_model
        print(f"Using model: {model_id}")
        
        try:
            # Get the inference client
            client = OpenAI(
                api_key=self.kluster_key, 
                base_url="https://api.kluster.ai/v1"
            )

            # Build the conversation
            messages = [
                {"role": "system", "content": system_message},
            ]

            if knowledge_context:
                messages.append({"role": "system", "content": knowledge_context})

            # Add chat history
            if chat_history:
                messages.extend(chat_history)  # Add the chat history objects directly

            # Add user prompt
            messages.append({"role": "user", "content": user_text})

            # Call the chat completion endpoint
            response_obj = client.chat.completions.create(
                model=model_id,  # Use the determined model_id
                messages=messages,
                temperature=0.4,
                max_tokens=512,
            )

            # Extract the response
            response = response_obj.choices[0].message.content.strip()
            
            # Clean up response
            if "AI:" in response:
                response = response.split("AI:")[-1].strip()
                
            # Update chat history
            chat_history.append({"role": "user", "content": user_text})
            chat_history.append({"role": "assistant", "content": response})
            
            return response, chat_history
            
        except Exception as e:
            print(f"Error in API key chat method: {str(e)}")
            print(traceback.format_exc())
            
            # Provide a fallback response
            fallback_response = "I'm sorry, I encountered an error while processing your request. Please try again later."
            chat_history.append({"role": "user", "content": user_text})
            chat_history.append({"role": "assistant", "content": fallback_response})
            return fallback_response, chat_history