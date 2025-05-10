from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app import __version__
# from app.middleware.request_logger import RequestLoggingMiddleware
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

# app.add_middleware(RequestLoggingMiddleware)
# Update CORS settings to specify frontend origins
# Note: Using ["*"] with allow_credentials=True is not allowed for security reasons
logger.info(f"Cors origins: {settings.CORS_ORIGINS}")
origins = [
    "http://localhost:3000",
    "http://localhost",
    "https://non-chatbot.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Include API router (existing code)
app.include_router(api_router)

# Mount static files (existing code)
app.mount("/static", StaticFiles(directory="static"), name="static")