from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: UUID4
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Return to client"""
    pass


class UserInDB(UserInDBBase):
    """Stored in DB"""
    password: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str