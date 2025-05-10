from typing import Optional, Annotated, Dict, Any, Tuple
from uuid import UUID
from jose import jwt, JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Response, Depends, Cookie
from fastapi.security import OAuth2PasswordBearer

from app.db import get_session
from app.daos.user import UserDAO
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, TokenPayload
from app.services.utils import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, UtilsService
from app.settings import settings


class UserService:
    def __init__(self):
        self.user_dao = UserDAO()
        self.utils = UtilsService()

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password"""
        user = await self.user_dao.get_by_email(db, email)
        if not user or not self.utils.verify_password(password, user.password):
            return None
        return user

    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if email already exists
        existing_user = await self.user_dao.get_by_email(db, user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        return await self.user_dao.create(db, user_create)

    async def get_user(self, db: AsyncSession, user_id: UUID) -> User:
        """Get a user by ID"""
        user = await self.user_dao.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email"""
        return await self.user_dao.get_by_email(db, email)

    async def update_user(self, db: AsyncSession, user_id: UUID, user_update: UserUpdate) -> User:
        """Update a user"""
        user = await self.user_dao.update(db, user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def delete_user(self, db: AsyncSession, user_id: UUID) -> User:
        """Delete a user"""
        user = await self.user_dao.delete(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    def create_tokens(self, user_id: UUID) -> Tuple[str, str]:
        """Create access and refresh tokens for a user"""
        access_token = self.utils.create_access_token(user_id)
        refresh_token = self.utils.create_refresh_token(user_id)
        return access_token, refresh_token

    def set_auth_cookies(self, response: Response, user_id: UUID) -> Dict[str, str]:
        """Set authentication cookies on response and return token data"""
        # Create both tokens
        access_token, refresh_token = self.create_tokens(user_id)
        
        # Common cookie settings
        cookie_settings = self.utils.get_token_settings()
        
        # Set access token cookie (shorter expiry)
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            path="/",
            **cookie_settings
        )
        
        # Set refresh token cookie (longer expiry)
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,  # Convert days to seconds
            path="/",
            **cookie_settings
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_auth_tokens(
        self,
        db: AsyncSession,
        response: Response,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh both tokens using a valid refresh token
        
        Args:
            db: Database session
            response: FastAPI response object to set cookies on
            refresh_token: The refresh token to validate
            
        Returns:
            Dictionary with token information and success message
            
        Raises:
            HTTPException: If refresh token is invalid or user no longer exists
        """
        try:
            # Validate refresh token
            payload = self.utils.decode_token(refresh_token)
            
            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extract user ID
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            user_id = UUID(user_id_str)
            
            # Verify user still exists
            user = await self.get_user(db, user_id)
            
            # Create new tokens and set cookies
            tokens = self.set_auth_cookies(response, user_id)
            
            return {
                "message": "Tokens refreshed successfully",
                "user_id": str(user_id),
                **tokens
            }
            
        except (JWTError, ValueError) as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def clear_auth_cookies(self, response: Response) -> None:
        """Clear authentication cookies"""
        response.delete_cookie(key=ACCESS_COOKIE_NAME, path="/")
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/")
        
    async def get_current_user(
        self, 
        db: AsyncSession,
        access_token: Optional[str] = Cookie(None, alias=ACCESS_COOKIE_NAME),
        refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME)
    ) -> User:
        """
        Get the current user from the access token cookie
        Falls back to refresh token if access token is invalid
        
        Args:
            db: Database session
            access_token: The access token cookie
            refresh_token: The refresh token cookie
            
        Returns:
            The authenticated user
            
        Raises:
            HTTPException: If authentication fails
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # Try access token first
        if access_token:
            try:
                payload = jwt.decode(
                    access_token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM]
                )
                user_id_str = payload.get("sub")
                token_type = payload.get("type")
                
                if user_id_str and token_type == "access":
                    user_id = UUID(user_id_str)
                    user = await self.user_dao.get(db, user_id)
                    if user:
                        return user
            except (JWTError, ValueError):
                # Access token failed, try refresh token if available
                pass
        
        # Try refresh token as fallback
        if refresh_token:
            try:
                payload = jwt.decode(
                    refresh_token, 
                    settings.SECRET_KEY, 
                    algorithms=[settings.ALGORITHM]
                )
                user_id_str = payload.get("sub")
                token_type = payload.get("type")
                
                if user_id_str and token_type == "refresh":
                    user_id = UUID(user_id_str)
                    user = await self.user_dao.get(db, user_id)
                    if user:
                        # User authenticated via refresh token
                        # Frontend should call /refresh-token endpoint to refresh access token
                        return user
            except (JWTError, ValueError):
                pass
                
        # No valid token found
        raise credentials_exception


# Create a singleton instance
user_service = UserService()


# Create dependencies for current user
async def get_current_user(
    db: AsyncSession = Depends(get_session),
    access_token: Optional[str] = Cookie(None, alias=ACCESS_COOKIE_NAME),
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE_NAME),
) -> User:
    return await user_service.get_current_user(db, access_token, refresh_token)


# Create a type annotation for use in route function parameters
CurrentUserDep = Annotated[User, Depends(get_current_user)]