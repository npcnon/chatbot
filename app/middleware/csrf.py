from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyCookie
from fastapi.responses import JSONResponse
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# These methods should be protected by CSRF verification
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# The header where CSRF token will be sent from the frontend
CSRF_HEADER = "X-CSRF-Token"

class CSRFProtection:
    """
    Dependency that verifies CSRF token for mutating requests
    """
    async def __call__(
        self, 
        request: Request, 
        csrf_token_cookie: Optional[str] = None,
    ) -> None:
        # Skip CSRF check for safe methods
        if request.method not in CSRF_PROTECTED_METHODS:
            return None
            
        # Get CSRF token from header
        csrf_token_header = request.headers.get(CSRF_HEADER)
        
        # Get CSRF token from cookie
        if not csrf_token_cookie:
            csrf_token_cookie = request.cookies.get("csrf_token")
            
        # If we don't have both tokens, deny access
        if not csrf_token_header or not csrf_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid",
            )
            
        # Verify tokens match
        if csrf_token_header != csrf_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token verification failed",
            )
            
        return None


# Create an instance to use as a dependency
csrf_protection = CSRFProtection()


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware that verifies CSRF protection for all mutating requests
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip CSRF check for safe methods
        if request.method not in CSRF_PROTECTED_METHODS:
            return await call_next(request)
            
        # Skip CSRF check for login and refresh endpoints
        path = request.url.path
        if path.endswith("/token") or path.endswith("/refresh"):
            return await call_next(request)
            
        # Get CSRF token from header
        csrf_token_header = request.headers.get(CSRF_HEADER)
        
        # Get CSRF token from cookie
        csrf_token_cookie = request.cookies.get("csrf_token")
        
        # If we don't have both tokens, deny access
        if not csrf_token_header or not csrf_token_cookie:
            # Use JSONResponse instead of Response for JSON content
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing or invalid"},
            )
            
        # Verify tokens match
        if csrf_token_header != csrf_token_cookie:
            # Use JSONResponse here as well
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token verification failed"},
            )
            
        # Continue processing the request
        return await call_next(request)