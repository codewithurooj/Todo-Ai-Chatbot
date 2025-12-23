"""Health check endpoint for monitoring system status"""
from fastapi import APIRouter, status
from sqlmodel import Session, select
from app.database import get_session, engine
from app.config import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint with component status

    Checks:
    - API responsiveness
    - Database connectivity
    - OpenAI API availability

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "components": {
                "api": "ok",
                "database": "ok" | "error",
                "openai": "ok" | "error"
            }
        }
    """
    components = {
        "api": "ok",
        "database": "unknown",
        "openai": "unknown"
    }

    overall_status = "healthy"

    # Check database
    try:
        with Session(engine) as session:
            # Simple query to verify database connection
            session.exec(select(1))
        components["database"] = "ok"
        logger.debug("Database health check: OK")
    except Exception as e:
        components["database"] = "error"
        overall_status = "unhealthy"
        logger.error(f"Database health check failed: {str(e)}")

    # Check OpenAI API
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Lightweight API call to verify connectivity
        client.models.list()
        components["openai"] = "ok"
        logger.debug("OpenAI health check: OK")
    except Exception as e:
        components["openai"] = "error"
        # OpenAI failure is degraded, not unhealthy (API still works)
        if overall_status == "healthy":
            overall_status = "degraded"
        logger.error(f"OpenAI health check failed: {str(e)}")

    return {
        "status": overall_status,
        "components": components,
        "version": settings.PROJECT_VERSION
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint

    Returns:
        Basic API information
    """
    return {
        "message": f"{settings.PROJECT_NAME} - Phase 3",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


__all__ = ["router"]
