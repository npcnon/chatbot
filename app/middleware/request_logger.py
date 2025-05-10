from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger
import time
import json

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Clone request body safely
        body = await request.body()
        req_body = body.decode("utf-8", errors="replace")

        # Trick to re-inject body into the stream
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive

        original_response = await call_next(request)

        # Capture response body
        resp_body = b""
        async for chunk in original_response.body_iterator:
            resp_body += chunk

        # Extract all original headers, preserving multiple Set-Cookie headers
        headers_dict = {}
        cookies = []
        
        for name, value in original_response.headers.items():
            if name.lower() == "set-cookie":
                # Store cookies separately to handle them specially
                cookies.append(value)
            else:
                headers_dict[name] = value

        # Reconstruct response
        response = Response(
            content=resp_body,
            status_code=original_response.status_code,
            headers=headers_dict,
            media_type=original_response.media_type
        )
        
        # Add each cookie as a separate header
        for cookie in cookies:
            response.headers.append("Set-Cookie", cookie)

        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
        logger.debug(f"Request body: {req_body}")
        logger.debug(f"Response body: {resp_body.decode('utf-8', errors='replace')}")

        return response