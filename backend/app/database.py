"""Database setup and session management"""
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool
from typing import Generator
from app.config import settings
import os

# Determine if we're using SQLite (test mode) or PostgreSQL (production)
is_sqlite = settings.DATABASE_URL.startswith('sqlite://')
is_testing = os.getenv("TESTING", "").lower() == "true"

# Create engine with appropriate settings based on database type
if is_sqlite or is_testing:
    # SQLite configuration (for testing)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL configuration (for production)
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,  # Max 5 concurrent connections
        max_overflow=10,  # Allow 10 additional connections if pool full
        pool_timeout=30,  # Wait 30s for available connection
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.DEBUG,  # SQL logging in development
    )


def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection"""
    with Session(engine) as session:
        yield session
