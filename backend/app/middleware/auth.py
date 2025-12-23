"""JWT authentication and rate limiting middleware"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Make HTTPBearer optional so we can also check cookies
security = HTTPBearer(auto_error=False)

# Rate limiting configuration
RATE_LIMITS = {
    "requests_per_hour": 100,
    "requests_per_minute": 20
}

# In-memory rate limit storage (for development)
# Format: {user_id: {"hour": [(timestamp, count)], "minute": [(timestamp, count)]}}
rate_limit_store: Dict[str, Dict[str, List[datetime]]] = defaultdict(lambda: {"hour": [], "minute": []})


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Extract and validate JWT token from either Authorization header or cookies.

    Supports two authentication methods:
    1. Authorization: Bearer <token> header (preferred for API clients)
    2. better-auth.session_token cookie (used by Better Auth in browser)

    Args:
        request: FastAPI Request object to access cookies
        credentials: Optional HTTP Bearer token credentials

    Returns:
        str: User ID from JWT token

    Raises:
        HTTPException: If token is invalid, expired, or missing user_id
    """
    token = None

    # Try to get token from Authorization header first (for API compatibility)
    if credentials:
        token = credentials.credentials
    # If not in header, try to get from Better Auth session cookie
    elif "better-auth.session_token" in request.cookies:
        token = request.cookies.get("better-auth.session_token")

    # No token found in either location
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=["HS256"]
        )

        # Extract user_id from 'sub' claim
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def clean_old_requests(requests: List[datetime], window: timedelta) -> List[datetime]:
    """
    Remove timestamps older than the window from the request list

    Args:
        requests: List of request timestamps
        window: Time window to keep (e.g., timedelta(hours=1))

    Returns:
        Cleaned list with only recent timestamps
    """
    now = datetime.utcnow()
    cutoff = now - window
    return [ts for ts in requests if ts > cutoff]


async def check_rate_limit(
    user_id: str = Depends(get_current_user_id)
) -> str:
    """
    Check if user has exceeded rate limits

    Rate limits:
    - 100 requests per hour
    - 20 requests per minute

    Args:
        user_id: Authenticated user ID from JWT

    Returns:
        str: User ID if rate limit not exceeded

    Raises:
        HTTPException 429: If rate limit is exceeded
    """
    now = datetime.utcnow()

    # Get user's request history
    user_requests = rate_limit_store[user_id]

    # Clean old requests (older than 1 hour)
    user_requests["hour"] = clean_old_requests(
        user_requests["hour"],
        timedelta(hours=1)
    )
    user_requests["minute"] = clean_old_requests(
        user_requests["minute"],
        timedelta(minutes=1)
    )

    # Check hourly limit
    hourly_count = len(user_requests["hour"])
    if hourly_count >= RATE_LIMITS["requests_per_hour"]:
        # Calculate when the oldest request will expire
        oldest_request = min(user_requests["hour"])
        retry_after = int((oldest_request + timedelta(hours=1) - now).total_seconds())

        logger.warning(f"Rate limit exceeded for user {user_id}: {hourly_count} requests in last hour")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Too many requests. You can make up to 100 requests per hour.",
                "retry_after": retry_after,
                "limit": RATE_LIMITS["requests_per_hour"],
                "window": "hour"
            }
        )

    # Check per-minute limit
    minute_count = len(user_requests["minute"])
    if minute_count >= RATE_LIMITS["requests_per_minute"]:
        # Calculate when the oldest request will expire
        oldest_request = min(user_requests["minute"])
        retry_after = int((oldest_request + timedelta(minutes=1) - now).total_seconds())

        logger.warning(f"Rate limit exceeded for user {user_id}: {minute_count} requests in last minute")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Too many requests. You can make up to 20 requests per minute.",
                "retry_after": retry_after,
                "limit": RATE_LIMITS["requests_per_minute"],
                "window": "minute"
            }
        )

    # Record this request
    user_requests["hour"].append(now)
    user_requests["minute"].append(now)

    logger.debug(f"Rate limit check passed for user {user_id}: {hourly_count + 1}/hour, {minute_count + 1}/minute")

    return user_id


__all__ = ["get_current_user_id", "check_rate_limit", "RATE_LIMITS"]
