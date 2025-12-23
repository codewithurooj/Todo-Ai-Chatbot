"""FastAPI application entry point with middleware and routing"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, create_db_and_tables
from app.routes import health, tasks, chat, conversations
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.middleware.logging import RequestLoggingMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events

    Startup:
    - Validate production configuration
    - Create database tables
    - Initialize connections

    Shutdown:
    - Clean up resources
    """
    # Startup
    logger.info("Starting application...")

    # Validate production configuration
    try:
        settings.validate_production_config()
        logger.info("Configuration validation passed")
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        # Don't fail startup, but log the warning
        logger.warning("Continuing with potentially invalid configuration")

    logger.info(f"Creating database tables...")
    create_db_and_tables()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered conversational task management API (Phase 3)",
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
# IMPORTANT: For production, set CORS_ORIGINS environment variable to include your frontend domain
# Example: CORS_ORIGINS="https://your-app.vercel.app,https://your-app-prod.vercel.app"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(conversations.router)

logger.info(f"{settings.PROJECT_NAME} initialized")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
