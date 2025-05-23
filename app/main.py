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



app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0"
)

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"message": "Welcome to the base URL"}


# Update CORS settings to specify frontend origins
# Note: Using ["*"] with allow_credentials=True is not allowed for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
        "api-key" 
    ],
    expose_headers=["Content-Type", "Set-Cookie"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Add CSRF protection middleware
# app.add_middleware(CSRFMiddleware)

# Include API router (existing code)
app.include_router(api_router)

# Mount static files (existing code)
app.mount("/static", StaticFiles(directory="static"), name="static")