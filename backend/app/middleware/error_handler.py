"""Global error handling middleware"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Union

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error response format

    Follows format specified in contracts/agent-orchestrator.md:
    {
        "error": "<ErrorType>",
        "message": "<user-friendly error message>",
        "retry_after": <optional seconds> // for rate limiting
    }

    Args:
        request: FastAPI request object
        exc: HTTP exception

    Returns:
        JSONResponse with error details
    """
    # Check if detail is already a structured dict (e.g., from rate limiting)
    if isinstance(exc.detail, dict):
        # Detail is already formatted (e.g., from check_rate_limit)
        # Just sanitize the message field
        content = exc.detail.copy()
        if "message" in content and isinstance(content["message"], str):
            content["message"] = sanitize_input(content["message"])
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )

    # Sanitize error message to prevent XSS attacks
    sanitized_message = sanitize_input(str(exc.detail)) if exc.detail else "An error occurred"

    # Map HTTP status codes to error types per agent-orchestrator.md
    error_type_mapping = {
        400: "ValidationError",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        429: "RateLimitExceeded",
        500: "InternalServerError",
        502: "BadGateway",
        503: "ServiceUnavailable",
        504: "GatewayTimeout"
    }

    error_type = error_type_mapping.get(exc.status_code, "HttpError")

    # Build response content
    content = {
        "error": error_type,
        "message": sanitized_message
    }

    # Add retry_after for rate limiting (429) from headers if present
    if exc.status_code == 429 and hasattr(exc, 'headers') and 'Retry-After' in exc.headers:
        try:
            content["retry_after"] = int(exc.headers['Retry-After'])
        except (ValueError, TypeError):
            pass

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors with consistent error response format

    Follows format specified in contracts/agent-orchestrator.md:
    {
        "error": "ValidationError",
        "message": "<user-friendly error message>",
        "details": [<optional validation error details>]
    }

    Args:
        request: FastAPI request object
        exc: Validation exception

    Returns:
        JSONResponse with validation error details
    """
    # Sanitize validation error details to prevent XSS attacks
    errors = exc.errors()
    sanitized_errors = []
    for error in errors:
        sanitized_error = {}
        for key, value in error.items():
            if isinstance(value, str):
                sanitized_error[key] = sanitize_input(value)
            elif isinstance(value, (list, tuple)):
                # Sanitize list elements if they're strings
                sanitized_error[key] = [
                    sanitize_input(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized_error[key] = value
        sanitized_errors.append(sanitized_error)

    # Generate user-friendly message from first error
    user_message = "Request validation failed"
    if sanitized_errors:
        first_error = sanitized_errors[0]
        field = " → ".join(str(loc) for loc in first_error.get("loc", [])) if "loc" in first_error else "field"
        error_msg = first_error.get("msg", "invalid value")
        user_message = f"Validation error in {field}: {error_msg}"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": user_message,
            "details": sanitized_errors
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with consistent error response format

    Follows format specified in contracts/agent-orchestrator.md:
    {
        "error": "InternalServerError",
        "message": "Internal server error"
    }

    Args:
        request: FastAPI request object
        exc: Any unhandled exception

    Returns:
        JSONResponse with generic error message
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "Internal server error"
        }
    )


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks

    Removes null bytes and HTML-escapes special characters to prevent:
    - XSS (Cross-Site Scripting) attacks
    - Injection attacks
    - Null byte injection

    Args:
        text: Raw user input

    Returns:
        Sanitized text safe for output
    """
    # Remove null bytes (prevents null byte injection)
    text = text.replace('\x00', '')

    # HTML escape special characters (prevents XSS)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')

    return text


__all__ = [
    "http_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
    "sanitize_input"
]
