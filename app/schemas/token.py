from pydantic import BaseModel
from app.schemas.user import User

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPair(BaseModel):
    """Token pair response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh endpoint"""
    refresh_token: str


class TokenResponse(TokenPair):
    """Token response with user information"""
    user: User


class RefreshResponse(BaseModel):
    """Response schema for token refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    message: str
    user_id: str