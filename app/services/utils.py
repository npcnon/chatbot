from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Cookie, Request
from fastapi.security import APIKeyCookie

from app.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cookie extractors for JWT tokens
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


class UtilsService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password for storing"""
        return pwd_context.hash(password)

    @staticmethod
    def create_token(subject: Union[str, UUID], token_type: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token for a user
        
        Args:
            subject: The subject (usually user ID)
            token_type: Either "access" or "refresh"
            expires_delta: Optional custom expiration time
            
        Returns:
            The encoded JWT token
        """
        if expires_delta is None:
            if token_type == "access":
                expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            else:  # refresh token
                expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
                
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "exp": expire, 
            "sub": str(subject),
            "type": token_type
        }
        
        return jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )

    @staticmethod
    def create_access_token(subject: Union[str, UUID], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token"""
        return UtilsService.create_token(subject, "access", expires_delta)

    @staticmethod
    def create_refresh_token(subject: Union[str, UUID], expires_delta: Optional[timedelta] = None) -> str:
        """Create a refresh token"""
        return UtilsService.create_token(subject, "refresh", expires_delta)
        
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token
        
        Args:
            token: JWT token to decode
            
        Returns:
            The decoded payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_token_settings() -> Dict[str, Any]:
        """Get common cookie settings for JWT tokens"""
        return {
            "httponly": True,
            "secure": settings.COOKIE_SECURE,  # Set to True in production with HTTPS
            "samesite": settings.COOKIE_SAMESITE  
        }