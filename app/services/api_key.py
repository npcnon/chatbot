import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID

from app.daos.api_key import ApiKeyDao
from app.models.api_key import ApiKey


class ApiKeyService:
    def __init__(self, api_key_dao: ApiKeyDao):
        self.api_key_dao = api_key_dao

    def _hash_key(self, key: str) -> str:
        """Create a hash of the API key for secure storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    def _generate_api_key(self) -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(32)

    async def create_api_key(self, user_id: UUID, name: str, description: Optional[str] = None, 
                           expires_in_days: Optional[int] = None) -> tuple[str, ApiKey]:
        """
        Create a new API key for a user.
        
        Returns:
            tuple: (raw_api_key, api_key_model)
        """
        # Generate a new API key
        raw_key = self._generate_api_key()
        key_hash = self._hash_key(raw_key)
        
        # Set expiration if specified
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        # Create the API key record
        api_key_data = {
            "user_id": user_id,
            "key_hash": key_hash,
            "name": name,
            "description": description,
            "is_active": True,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Store the API key
        api_key = await self.api_key_dao.create(api_key_data)
        
        # Return both the raw key (to be shown to the user once) and the model
        return raw_key, api_key

    async def validate_api_key(self, api_key: str) -> Optional[ApiKey]:
        """
        Validate an API key and return the associated API key record if valid.
        Also updates the usage statistics.
        """
        if not api_key:
            return None
            
        # Hash the API key
        key_hash = self._hash_key(api_key)
        
        # Look up the API key in the database
        api_key_record = await self.api_key_dao.get_by_key_hash(key_hash)
        
        # Check if the API key exists and is valid
        if not api_key_record:
            return None
            
        if not api_key_record.is_active:
            return None
            
        if api_key_record.is_expired:
            return None
            
        # Update usage statistics
        await self.api_key_dao.update_usage(api_key_record.id)
        
        return api_key_record

    async def get_user_api_keys(self, user_id: UUID) -> List[ApiKey]:
        """Get all API keys for a user"""
        return await self.api_key_dao.get_by_user_id(user_id)

    async def revoke_api_key(self, api_key_id: UUID) -> bool:
        """Revoke an API key by setting is_active to False"""
        api_key = await self.api_key_dao.get_by_id(api_key_id)
        if not api_key:
            return False
            
        api_key.is_active = False
        await self.api_key_dao.session.commit()
        return True

    async def delete_api_key(self, api_key_id: UUID) -> bool:
        """Delete an API key"""
        api_key = await self.api_key_dao.delete_by_id(api_key_id)
        return api_key is not None

    async def get_custom_ai_by_api_key(self, api_key: str):
        """Get the CustomAI associated with an API key through the user relationship"""
        api_key_record = await self.validate_api_key(api_key)
        if not api_key_record:
            return None
            
        # Return the user's custom AI
        return api_key_record.user.custom_ai if api_key_record.user else None