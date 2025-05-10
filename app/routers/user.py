from fastapi import APIRouter, Depends, Response, Request, Form, Cookie, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.token import Token
from app.schemas.user import UserIn, UserOut, ChangePasswordIn
from app.services.user import UserService, CurrentUserDep

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register", status_code=201)
async def register_user(
    user_data: UserIn,
    session: AsyncSession = Depends(get_session),
):
    user_service = UserService(session)
    return await user_service.register_user(user_data)


@router.post("/token", response_model=Token)
async def login(
    response: Response,
    login_data: LoginRequest,  # Change to accept JSON request body
    session: AsyncSession = Depends(get_session),
):
    """Login endpoint that sets cookies and returns tokens"""
    user_service = UserService(session)
    token = await user_service.login(login_data.username, login_data.password, response)
    
    # Return tokens only
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    session: AsyncSession = Depends(get_session),
    refresh_token: str = Cookie(None),
):
    """Endpoint to refresh the access token"""
    user_service = UserService(session)
    return await user_service.refresh_token(refresh_token, response)


@router.post("/logout")
async def logout(
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """Logout endpoint that clears auth cookies"""
    user_service = UserService(session)
    return await user_service.logout(response)


@router.get("/me", response_model=UserOut)
async def get_current_user(current_user: CurrentUserDep):
    """Get current logged in user"""
    return UserOut.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordIn,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
):

    user_service = UserService(session)
    return await user_service.change_password(password_data, current_user)


# Admin routes - should be protected with additional role check
@router.get("/all", response_model=list[UserOut])
async def get_all_users(
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check here
    user_service = UserService(session)
    return await user_service.get_all_users()


@router.delete("/all")
async def delete_all_users(
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check here
    user_service = UserService(session)
    return await user_service.delete_all_users()


@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: str,
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check or self check here
    user_service = UserService(session)
    return await user_service.get_user_by_id(user_id)


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check or self check here
    user_service = UserService(session)
    return await user_service.delete_user_by_id(user_id)