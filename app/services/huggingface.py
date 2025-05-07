import os
from typing import List, Dict, Optional
from uuid import UUID
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.daos.custom_ai import CustomAIDao
from app.daos.personality import PersonalityDao
from app.daos.knowledge_base import KnowledgeBaseDao


load_dotenv()

class HuggingFaceService:
    """Service for interacting with HuggingFace models"""
    
    def __init__(self, 
                 custom_ai_dao: CustomAIDao, 
                 personality_dao: PersonalityDao,
                 knowledge_base_dao: KnowledgeBaseDao):
        self.custom_ai_dao = custom_ai_dao
        self.personality_dao = personality_dao
        self.knowledge_base_dao = knowledge_base_dao
        
    async def get_llm(self, model_id: str, max_tokens: int = 256, temperature: float = 0.1):
        """Get a HuggingFace language model instance"""
        return HuggingFaceEndpoint(
            repo_id=model_id,
            task="text-generation",
            max_new_tokens=max_tokens,
            temperature=temperature,
            token=os.getenv("HF_TOKEN")
        )
        
    async def chat(self, 
                 ai_id: UUID, 
                 user_text: str,
                 chat_history: Optional[List[Dict[str, str]]] = None) -> tuple:
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
        
        # Format chat history
        history_text = ""
        for message in chat_history:
            role = message["role"]
            content = message["content"]
            history_text += f"{role.capitalize()}: {content}\n"
            
        # Get the language model
        llm = await self.get_llm(
            model_id=custom_ai.ai_model,
            max_tokens=256,
            temperature=0.1
        )
        
        # Create the prompt
        prompt = PromptTemplate.from_template(
            (
                "[INST] {system_message}\n{knowledge_context}\n"
                "\nConversation:\n{chat_history}\n"
                "\nUser: {user_text}\n [/INST]"
                "\nAI:"
            )
        )
        
        # Create the chain
        chain = prompt | llm.bind(skip_prompt=True) | StrOutputParser()
        
        # Generate response
        response = await chain.ainvoke({
            "system_message": system_message,
            "knowledge_context": knowledge_context,
            "chat_history": history_text,
            "user_text": user_text
        })
        
        # Clean up response
        if "AI:" in response:
            response = response.split("AI:")[-1].strip()
            
        # Update chat history
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": response})
        
        return response, chat_history