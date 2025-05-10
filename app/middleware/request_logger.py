from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger
import time

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Read request body
        req_body = await request.body()
        request._receive = lambda: {"type": "http.request", "body": req_body}

        response = await call_next(request)

        # Read response body
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk

        # Create a new response to replace the original
        response = Response(
            content=resp_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {time.time() - start_time:.2f}s")
        logger.debug(f"Request body: {req_body.decode('utf-8')}")
        logger.debug(f"Response body: {resp_body.decode('utf-8')}")

        return response
