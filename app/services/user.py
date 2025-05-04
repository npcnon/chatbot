from fastapi import Depends, HTTPException, status, Response, Cookie, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from uuid import UUID
from datetime import datetime, timedelta
from typing import Annotated, Optional

from jose import JWTError, jwt
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.daos import user
from app.db import get_session
from app.models.user import User as UserModel
from app.schemas.token import Token, TokenData
from app.schemas.user import ChangePasswordIn, UserIn, UserOut
from app.services.utils import UtilsService
from app.settings import settings


class UserService:
    @staticmethod
    async def register_user(user_data: UserIn, session: AsyncSession):
        user_exist = await UserService.user_email_exists(session, user_data.email)

        if user_exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with the given email already exists!!!",
            )

        user_data.password = UtilsService.get_password_hash(user_data.password)
        new_user = await user.UserDao(session).create(user_data.model_dump())
        logger.info(f"New user created successfully: {new_user}!!!")
        return JSONResponse(
            content={"message": "User created successfully"},
            status_code=status.HTTP_201_CREATED,
        )

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> UserModel | bool:
        _user = await user.UserDao(session).get_by_email(email)
        if not _user or not UtilsService.verify_password(password, _user.password):
            return False
        return _user

    @staticmethod
    async def user_email_exists(session: AsyncSession, email: str) -> UserModel | None:
        _user = await user.UserDao(session).get_by_email(email)
        return _user if _user else None

    @staticmethod
    async def login(form_data: OAuth2PasswordRequestForm, session: AsyncSession, response: Response) -> Token:
        _user = await UserService.authenticate_user(session, form_data.username, form_data.password)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = UtilsService.create_access_token(
            data={"sub": _user.email, "type": "access"}, 
            expires_delta=access_token_expires
        )
        
        # Create refresh token with longer expiration
        refresh_token_expires = timedelta(days=7)  # Typically longer than access token
        refresh_token = UtilsService.create_access_token(
            data={"sub": _user.email, "type": "refresh"},
            expires_delta=refresh_token_expires
        )

        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # For HTTPS
            samesite="lax",  # Prevents CSRF
            max_age=access_token_expires.total_seconds(),
            path="/"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=refresh_token_expires.total_seconds(),
            path="/api/v1/user/refresh"  # Only sent to refresh endpoint
        )
        
        # Also return tokens in the response body for initial setup
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
        return Token(**token_data)

    @staticmethod
    async def refresh_token(
        refresh_token: str = Cookie(None),
        session: AsyncSession = Depends(get_session),
        response: Response = None,
    ) -> Token:
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
                
            _user = await user.UserDao(session).get_by_email(email=email)
            if not _user:
                raise credentials_exception
                
            # Create new access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = UtilsService.create_access_token(
                data={"sub": _user.email, "type": "access"}, 
                expires_delta=access_token_expires
            )
            
            # Set new access token in cookie
            if response:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=access_token_expires.total_seconds(),
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

    @staticmethod
    async def logout(response: Response):
        """
        Clear authentication cookies
        """
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/v1/user/refresh")
        
        return JSONResponse(
            content={"message": "Logged out successfully"},
            status_code=status.HTTP_200_OK,
        )

    @staticmethod
    async def get_current_user(
        session: AsyncSession = Depends(get_session),
        access_token: str = Cookie(None),
    ) -> UserModel:
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
            
        _user = await user.UserDao(session).get_by_email(email=token_data.email)
        if not _user:
            raise credentials_exception
            
        return _user

    @staticmethod
    async def get_all_users(session: AsyncSession) -> list[UserOut]:
        all_users = await user.UserDao(session).get_all()
        return [UserOut.model_validate(_user) for _user in all_users]

    @staticmethod
    async def delete_all_users(session: AsyncSession):
        await user.UserDao(session).delete_all()
        return JSONResponse(
            content={"message": "All users deleted successfully!!!"},
            status_code=status.HTTP_200_OK,
        )

    @staticmethod
    async def change_password(
        password_data: ChangePasswordIn,
        current_user: UserModel,
        session: AsyncSession = Depends(get_session),
    ):
        if not UtilsService.verify_password(password_data.old_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password!!!",
            )
        current_user.password = UtilsService.get_password_hash(password_data.new_password)
        session.add(current_user)
        await session.commit()
        return JSONResponse(
            content={"message": "Password updated successfully!!!"},
            status_code=status.HTTP_200_OK,
        )

    @staticmethod
    async def get_user_by_id(user_id: UUID, session: AsyncSession) -> UserOut:
        _user = await user.UserDao(session).get_by_id(user_id)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with the given id does not exist!!!",
            )
        return UserOut.model_validate(_user)

    @staticmethod
    async def delete_user_by_id(user_id: UUID, session: AsyncSession):
        _user = await user.UserDao(session).delete_by_id(user_id)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with the given id does not exist!!!",
            )
        return JSONResponse(
            content={"message": "User deleted successfully!!!"},
            status_code=status.HTTP_200_OK,
        )


CurrentUserDep = Annotated[UserModel, Depends(UserService.get_current_user)]