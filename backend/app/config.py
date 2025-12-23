"""Application configuration management"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
from functools import lru_cache
import sys
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str

    # Authentication
    BETTER_AUTH_SECRET: str
    BETTER_AUTH_URL: str = ""

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # MCP Server
    MCP_SERVER_NAME: str = "todo-chatbot-mcp"
    MCP_SERVER_VERSION: str = "1.0.0"

    # CORS settings
    # Comma-separated list of allowed origins (supports environment-specific configuration)
    # Example: "http://localhost:3000,https://your-app.vercel.app,https://your-app-prod.vercel.app"
    # Note: Wildcards like "https://*.vercel.app" are NOT supported by CORS spec
    # You must specify each origin explicitly
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into list of origins"""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Todo AI Chatbot API"
    PROJECT_VERSION: str = "3.0.0"

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format"""
        import os

        if not v:
            raise ValueError("DATABASE_URL is required")

        # Allow SQLite in test mode
        is_testing = os.getenv("TESTING", "").lower() == "true"
        if is_testing and v.startswith('sqlite://'):
            return v

        # Check for PostgreSQL protocol in production/development
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgres://. "
                "SQLite and other databases are not supported in production. "
                f"For testing, set TESTING=true environment variable."
            )

        # Check for sensitive info in URL (warn, don't fail)
        if 'password' in v.lower() and v.startswith('postgresql://'):
            logger.warning(
                "Database URL contains embedded password. "
                "Consider using environment-specific secrets management."
            )

        return v

    @field_validator('BETTER_AUTH_SECRET')
    @classmethod
    def validate_auth_secret(cls, v: str) -> str:
        """Validate BETTER_AUTH_SECRET meets security requirements"""
        if not v:
            raise ValueError("BETTER_AUTH_SECRET is required")

        # Minimum length requirement
        MIN_LENGTH = 32
        if len(v) < MIN_LENGTH:
            raise ValueError(
                f"BETTER_AUTH_SECRET must be at least {MIN_LENGTH} characters for security. "
                f"Current length: {len(v)}. "
                f"Generate a secure secret: openssl rand -base64 32"
            )

        # Warn about common insecure values
        INSECURE_VALUES = [
            'your-secret-key-here',
            'your-secret-key-here-min-32-chars',
            'change-me',
            'secret',
            'password',
            '12345678901234567890123456789012'
        ]
        if v.lower() in [s.lower() for s in INSECURE_VALUES]:
            raise ValueError(
                "BETTER_AUTH_SECRET appears to be a placeholder value. "
                "Please generate a secure secret: openssl rand -base64 32"
            )

        return v

    @field_validator('OPENAI_API_KEY')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OPENAI_API_KEY format"""
        if not v:
            raise ValueError("OPENAI_API_KEY is required")

        # Check for valid OpenAI key format (starts with sk-)
        if not v.startswith('sk-'):
            logger.warning(
                "OPENAI_API_KEY should start with 'sk-'. "
                "Verify this is a valid OpenAI API key from platform.openai.com"
            )

        # Check minimum length (OpenAI keys are typically 51+ chars)
        if len(v) < 20:
            logger.warning(
                f"OPENAI_API_KEY seems unusually short ({len(v)} chars). "
                "Verify this is a complete API key."
            )

        return v

    @field_validator('CORS_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS_ORIGINS configuration"""
        if not v:
            logger.warning(
                "CORS_ORIGINS is empty. Defaulting to http://localhost:3000. "
                "For production, set CORS_ORIGINS to your frontend URL."
            )
            return "http://localhost:3000"

        # Check for wildcards (not supported by CORS spec)
        if '*' in v:
            logger.warning(
                "CORS_ORIGINS contains wildcards (*). "
                "Wildcards like '*.vercel.app' are NOT supported by browsers. "
                "Specify each origin explicitly: 'https://app1.vercel.app,https://app2.vercel.app'"
            )

        return v

    def validate_production_config(self):
        """
        Validate configuration for production deployment

        Call this method during application startup to ensure
        production-critical settings are properly configured.

        Raises:
            ValueError: If production configuration is invalid
        """
        # Check if DEBUG is disabled in production
        if not self.DEBUG:
            logger.info("Production mode detected (DEBUG=false)")

            # Warn about development-like DATABASE_URL
            if 'localhost' in self.DATABASE_URL or '127.0.0.1' in self.DATABASE_URL:
                logger.warning(
                    "DATABASE_URL points to localhost but DEBUG=false. "
                    "Ensure you're using a production database (e.g., Neon, AWS RDS)."
                )

            # Check CORS configuration
            cors_list = self.cors_origins_list
            if any('localhost' in origin for origin in cors_list):
                logger.warning(
                    "CORS_ORIGINS includes localhost but DEBUG=false. "
                    "Ensure production frontend URL is configured."
                )

            # Verify HTTPS in production (for CORS origins)
            non_https = [origin for origin in cors_list if origin.startswith('http://') and 'localhost' not in origin]
            if non_https:
                logger.warning(
                    f"CORS_ORIGINS contains non-HTTPS origins in production: {non_https}. "
                    "Consider using HTTPS for security."
                )

        # Log configuration summary
        logger.info(f"Environment: {'development' if self.DEBUG else 'production'}")
        logger.info(f"Database: {self.DATABASE_URL.split('@')[0]}@***")  # Hide credentials
        logger.info(f"OpenAI Model: {self.OPENAI_MODEL}")
        logger.info(f"CORS Origins: {self.cors_origins_list}")
        logger.info(f"Log Level: {self.LOG_LEVEL}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
