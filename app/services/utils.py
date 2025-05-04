from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyCookie

from app.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# No longer needed for cookie-based auth
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/user/token")


class UtilsService:
    @staticmethod
    def verify_password(plain_password, hashed_password) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a CSRF token for forms"""
        from secrets import token_hex
        return token_hex(16)  # 32 character hex string

    @staticmethod
    def verify_csrf_token(request_token: str, stored_token: str) -> bool:
        """Verify that the CSRF token from the request matches the stored one"""
        if not request_token or not stored_token:
            return False
        return request_token == stored_token