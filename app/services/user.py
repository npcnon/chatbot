from fastapi import Depends, HTTPException, status, Response, Cookie, Request
from fastapi.responses import JSONResponse
from uuid import UUID
from datetime import datetime, timedelta
from typing import Annotated, Optional

from jose import JWTError, jwt
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.daos import user
from app.daos.custom_ai import CustomAIDao
from app.db import get_session
from app.models.user import User as UserModel
from app.schemas.custom_ai import CustomAICreate
from app.schemas.token import Token, TokenData
from app.schemas.user import ChangePasswordIn, UserIn, UserOut
from app.services.custom_ai import CustomAIService

from app.services.utils import UtilsService
from app.settings import settings


class UserService:

    def __init__(self, session: AsyncSession):
        self.user_dao = user.UserDao(session)
        self.session = session
        self.custom_ai_service = CustomAIService(session)
        
    async def register_user(self, user_data: UserIn):
        # Check existence before transaction
        user_exist = await self.user_email_exists(user_data.email)
        if user_exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        try:
            user_data.password = UtilsService.get_password_hash(user_data.password)
            new_user = await self.user_dao.create(user_data.model_dump())
            
            # Create custom AI
            custom_ai_data = CustomAICreate(user_id=new_user.id)
            await self.custom_ai_service.create_custom_ai(custom_ai_data)
            
            return JSONResponse(
                content={"message": "User created successfully"},
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Failed during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete registration"
            )

    async def authenticate_user(self, email: str, password: str) -> UserModel | bool:
        _user = await self.user_dao.get_by_email(email)
        if not _user or not UtilsService.verify_password(password, _user.password):
            return False
        return _user

    async def user_email_exists(self, email: str) -> UserModel | None:
        _user = await self.user_dao.get_by_email(email)
        return _user if _user else None

    async def login(self, username: str, password: str, response: Response) -> Token:
        """Login user, validate credentials, and return tokens."""
        _user = await self.authenticate_user(username, password)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        # The rest of your login logic remains the same
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = UtilsService.create_access_token(
            data={"sub": _user.email, "type": "access"}, 
            expires_delta=access_token_expires
        )
        
        refresh_token_expires = timedelta(days=7)
        refresh_token = UtilsService.create_access_token(
            data={"sub": _user.email, "type": "refresh"},
            expires_delta=refresh_token_expires
        )

        secure_cookies = getattr(settings, 'SECURE_COOKIES', False)
        samesite = getattr(settings, 'COOKIE_SAMESITE', 'lax')
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure_cookies,
            samesite=samesite,
            max_age=int(access_token_expires.total_seconds()),
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookies,
            samesite=samesite,
            max_age=int(refresh_token_expires.total_seconds()),
            path="/"
        )
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
        return Token(**token_data)


    async def refresh_token(self, refresh_token: str, response: Response = None) -> Token:
        """
        Endpoint to refresh the access token using a valid refresh token
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        if not refresh_token:
            raise credentials_exception
            
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if not email or token_type != "refresh":
                raise credentials_exception
                
            _user = await self.user_dao.get_by_email(email=email)
            if not _user:
                raise credentials_exception
                
            # Create new access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = UtilsService.create_access_token(
                data={"sub": _user.email, "type": "access"}, 
                expires_delta=access_token_expires
            )
            
            # Get cookie settings with fallbacks
            secure_cookies = getattr(settings, 'SECURE_COOKIES', False)
            samesite = getattr(settings, 'COOKIE_SAMESITE', 'lax')
            
            # Set new access token in cookie
            if response:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=secure_cookies,
                    samesite=samesite,
                    max_age=int(access_token_expires.total_seconds()),
                    path="/"
                )
            
            # Return new access token
            token_data = {
                "access_token": access_token,
                "token_type": "Bearer",
            }
            return Token(**token_data)
            
        except JWTError:
            raise credentials_exception

    async def logout(self, response: Response):
        """
        Clear authentication cookies
        """
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        
        return JSONResponse(
            content={"message": "Logged out successfully"},
            status_code=status.HTTP_200_OK,
        )

    async def get_current_user(self, access_token: str) -> UserModel:
        """
        Get the current user from the access token cookie
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        if not access_token:
            raise credentials_exception
            
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if not email or token_type != "access":
                raise credentials_exception
                
            token_data = TokenData(email=email)
        except JWTError:
            raise credentials_exception
            
        _user = await self.user_dao.get_by_email(email=token_data.email)
        if not _user:
            raise credentials_exception
            
        return _user

    async def get_all_users(self) -> list[UserOut]:
        all_users = await self.user_dao.get_all()
        return [UserOut.model_validate(_user) for _user in all_users]

    async def delete_all_users(self):
        await self.user_dao.delete_all()
        return JSONResponse(
            content={"message": "All users deleted successfully!!!"},
            status_code=status.HTTP_200_OK,
        )

    async def change_password(self, password_data: ChangePasswordIn, current_user: UserModel):
        if not UtilsService.verify_password(password_data.old_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password!!!",
            )
        current_user.password = UtilsService.get_password_hash(password_data.new_password)
        self.session.add(current_user)
        await self.session.commit()
        return JSONResponse(
            content={"message": "Password updated successfully!!!"},
            status_code=status.HTTP_200_OK,
        )

    async def get_user_by_id(self, user_id: UUID) -> UserOut:
        _user = await self.user_dao.get_by_id(user_id)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with the given id does not exist!!!",
            )
        return UserOut.model_validate(_user)

    async def delete_user_by_id(self, user_id: UUID):
        _user = await self.user_dao.delete_by_id(user_id)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with the given id does not exist!!!",
            )
        return JSONResponse(
            content={"message": "User deleted successfully!!!"},
            status_code=status.HTTP_200_OK,
        )


# Create a dependency for getting the current user
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    access_token: str = Cookie(None),
) -> UserModel:
    user_service = UserService(session)
    return await user_service.get_current_user(access_token)


CurrentUserDep = Annotated[UserModel, Depends(get_current_user)]