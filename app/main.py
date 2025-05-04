from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.routers.api_router import api_router
from app.middleware.csrf import CSRFMiddleware
from app.settings import settings

app = FastAPI(title=settings.PROJECT_NAME, version=__version__)

# Update CORS settings to specify frontend origins
# Note: Using ["*"] with allow_credentials=True is not allowed for security reasons
app.add_middleware(
    CORSMiddleware,
    # Replace ["*"] with your frontend URLs in production
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, "CORS_ORIGINS") else ["http://localhost:3000"],
    allow_credentials=True,  # Required for cookies to work
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Include API router (existing code)
app.include_router(api_router)

# Mount static files (existing code)
app.mount("/static", StaticFiles(directory="static"), name="static")