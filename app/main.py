from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app import __version__
from app.routers.api_router import api_router
from app.settings import settings
from app.db import engine 
from contextlib import asynccontextmanager
from loguru import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.success("✅ Successfully connected to the database.")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0", 
    lifespan=lifespan,
)


# Update CORS settings to specify frontend origins
# Note: Using ["*"] with allow_credentials=True is not allowed for security reasons
logger.info(f"CORS settings: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    # Replace ["*"] with your frontend URLs in production
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, "CORS_ORIGINS") else ["http://localhost:3000"],
    allow_credentials=True,  # Required for cookies to work
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSRF protection middleware
# app.add_middleware(CSRFMiddleware)

# Include API router (existing code)
app.include_router(api_router)

# Mount static files (existing code)
app.mount("/static", StaticFiles(directory="static"), name="static")