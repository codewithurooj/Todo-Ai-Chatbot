"""Request logging middleware with request ID tracking"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses

    Features:
    - Generates unique request_id for each request
    - Logs request method, path, client IP
    - Logs response status code and duration
    - Adds request_id to request state for use in other middleware/routes
    - Structured logging for easy parsing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response from the application
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request_id to request state (accessible in routes)
        request.state.request_id = request_id

        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log incoming request
        logger.info(
            f"[{request_id}] Incoming request",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] Response sent",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )

            # Add request_id to response headers for client-side tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration even for failed requests
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"[{request_id}] Request failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc)
                },
                exc_info=True
            )

            # Re-raise exception to be handled by error handlers
            raise


__all__ = ["RequestLoggingMiddleware"]
