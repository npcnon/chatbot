# app/middleware/request_logger.py

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

        response = await call_next(request)

        # Capture response body
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk

        # Reconstruct response
        response = Response(
            content=resp_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
        logger.debug(f"Request body: {req_body}")
        logger.debug(f"Response body: {resp_body.decode('utf-8', errors='replace')}")

        return response
