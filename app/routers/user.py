from fastapi import APIRouter, Depends, Response, Request, Form, Cookie, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.token import Token
from app.schemas.user import UserIn, UserOut, ChangePasswordIn
from app.services.user import UserService, CurrentUserDep
from app.services.utils import UtilsService
from app.middleware.csrf import csrf_protection

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", status_code=201)
async def register_user(
    user_data: UserIn,
    session: AsyncSession = Depends(get_session),
):
    return await UserService.register_user(user_data, session)


@router.post("/token", response_model=Token)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    """Login endpoint that sets cookies and returns tokens"""
    # Generate CSRF token for forms
    csrf_token = UtilsService.generate_csrf_token()
    
    # Set in cookie for CSRF protection
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be accessible from JS
        secure=True,     # HTTPS only
        samesite="lax",
        max_age=86400,   # 1 day
        path="/"
    )
    
    # Log in and set auth cookies
    token = await UserService.login(form_data, session, response)
    
    # Include CSRF token in response
    return {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "csrf_token": csrf_token
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    session: AsyncSession = Depends(get_session),
    refresh_token: str = Cookie(None),
):
    """Endpoint to refresh the access token"""
    return await UserService.refresh_token(refresh_token, session, response)


@router.post("/logout")
async def logout(response: Response):
    """Logout endpoint that clears auth cookies"""
    return await UserService.logout(response)


@router.get("/me", response_model=UserOut)
async def get_current_user(current_user: CurrentUserDep):
    """Get current logged in user"""
    return UserOut.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordIn,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_session),
    csrf_check: None = Depends(csrf_protection),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
):
    """Change user password with CSRF protection"""
    return await UserService.change_password(password_data, current_user, session)


# Admin routes - should be protected with additional role check
@router.get("/all", response_model=list[UserOut])
async def get_all_users(
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check here
    return await UserService.get_all_users(session)


@router.delete("/all")
async def delete_all_users(
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
    csrf_check: None = Depends(csrf_protection),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
):
    # TODO: Add role check here
    return await UserService.delete_all_users(session)


@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: str,
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
):
    # TODO: Add role check or self check here
    return await UserService.get_user_by_id(user_id, session)


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: CurrentUserDep,  # Only authenticated users
    session: AsyncSession = Depends(get_session),
    csrf_check: None = Depends(csrf_protection),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
):
    # TODO: Add role check or self check here
    return await UserService.delete_user_by_id(user_id, session)