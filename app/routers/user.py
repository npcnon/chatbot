from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db import get_session
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, LoginRequest
from app.schemas.token import TokenResponse, RefreshResponse, TokenRefreshRequest
from app.services.user import user_service, CurrentUserDep
from app.services.utils import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_session)
):
    """Create a new user"""
    return await user_service.create_user(db, user_create)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session)
):
    """
    Login and get JWT tokens as cookies
    
    Returns the tokens and user data in the response body
    and also sets the tokens as HTTP-only cookies
    """
    user = await user_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set JWT tokens as cookies
    tokens = user_service.set_auth_cookies(response, user.id)
    
    # Return tokens and user data in response body
    return {
        **tokens,
        "user": user
    }


@router.post("/logout", response_model=Dict[str, str])
async def logout(response: Response):
    """
    Logout and clear JWT token cookies
    
    Clears both access and refresh token cookies
    """
    await user_service.clear_auth_cookies(response)
    return {"message": "Successfully logged out"}


@router.post("/refresh-token", response_model=RefreshResponse)
async def refresh_token(
    response: Response,
    db: AsyncSession = Depends(get_session),
    refresh_token: str = Cookie(None, alias=REFRESH_COOKIE_NAME)
):
    """
    Refresh access and refresh tokens using a valid refresh token
    
    This endpoint can be called either:
    1. When the access token is about to expire
    2. When the access token has expired but refresh token is still valid
    
    Returns new tokens and sets them as cookies
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await user_service.refresh_auth_tokens(db, response, refresh_token)


@router.post("/refresh-token-body", response_model=RefreshResponse)
async def refresh_token_from_body(
    token_request: TokenRefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_session)
):
    """
    Alternative token refresh endpoint that takes the refresh token in the request body
    
    This is useful for clients that can't easily access cookies,
    such as mobile apps or certain frontend frameworks
    """
    return await user_service.refresh_auth_tokens(db, response, token_request.refresh_token)


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: CurrentUserDep):
    """Get current logged in user data"""
    return current_user


# Only administrators or the user themselves can access these endpoints
# These are commented out in the original code and kept that way here

# @router.get("/{user_id}", response_model=UserSchema)
# async def get_user(
#     user_id: UUID,
#     current_user: CurrentUserDep,
#     db: AsyncSession = Depends(get_session)
# ):
#     """Get a user by ID"""
#     # Only allow users to get their own info (could add admin role check here)
#     if current_user.id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to access this resource"
#         )
#     return await user_service.get_user(db, user_id)


# @router.put("/{user_id}", response_model=UserSchema)
# async def update_user(
#     user_id: UUID,
#     user_update: UserUpdate,
#     current_user: CurrentUserDep,
#     db: AsyncSession = Depends(get_session)
# ):
#     """Update a user"""
#     # Only allow users to update their own info
#     if current_user.id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to access this resource"
#         )
#     return await user_service.update_user(db, user_id, user_update)


# @router.delete("/{user_id}", response_model=UserSchema)
# async def delete_user(
#     user_id: UUID,
#     current_user: CurrentUserDep,
#     db: AsyncSession = Depends(get_session)
# ):
#     """Delete a user"""
#     # Only allow users to delete their own account
#     if current_user.id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to access this resource"
#         )
#     return await user_service.delete_user(db, user_id)