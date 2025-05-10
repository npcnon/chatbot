import os
import secrets
from functools import lru_cache
from typing import List, Optional


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_URL: str

    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATE_FORMAT: str = "%Y-%m-%d"

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CHATBOT(DEMO VERSION)"
    CORS_ORIGINS: List[str] = [  
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Cookie settings
    COOKIE_SAMESITE: str = "none"  
    COOKIE_SECURE: bool = True

@lru_cache
def get_settings():
    return Settings()  


settings = get_settings()