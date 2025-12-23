"""Pytest configuration and fixtures for backend tests

This module provides shared fixtures for:
- Test database setup/teardown
- FastAPI test client
- Mock OpenAI client
- Authentication tokens
- Test data factories
"""
import pytest
import os
from typing import Generator, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import jwt

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BETTER_AUTH_SECRET"] = "test-secret-key-min-32-chars-long-for-testing-purposes"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-not-used-in-tests"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://testserver"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"

# Import after setting env
from app.main import app
from app.database import get_session
from app.config import settings
from app.models.user import User
from app.models.task import Task
from app.models.conversation import Conversation
from app.models.message import Message


# ============================================================
# DATABASE FIXTURES
# ============================================================

@pytest.fixture(name="engine")
def engine_fixture():
    """
    Create in-memory SQLite engine for fast tests

    Uses StaticPool to maintain connection across test transactions.
    Alternative: Use separate PostgreSQL test database for production-like testing.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """
    Create a database session for each test

    Automatically rolls back transactions after each test to ensure isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def override_database_engine(engine):
    """
    Replace the global database engine with the test engine for ALL tests

    This ensures all database operations (handlers, routes, etc.) use the test database.
    """
    import app.database as db_module

    # Save original engine
    original_engine = db_module.engine

    # Replace with test engine
    db_module.engine = engine

    # Override get_session to use test engine
    def get_session_override():
        with Session(engine) as session:
            yield session

    # Override for FastAPI dependency injection
    app.dependency_overrides[get_session] = get_session_override

    yield

    # Restore original engine
    db_module.engine = original_engine

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with test database session

    Overrides the get_session dependency to use test database.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# AUTHENTICATION FIXTURES
# ============================================================

@pytest.fixture(name="test_user_id")
def test_user_id_fixture() -> str:
    """Return a consistent test user ID"""
    return "test-user-123"


@pytest.fixture(name="test_user_id_2")
def test_user_id_2_fixture() -> str:
    """Return a second test user ID for multi-user tests"""
    return "test-user-456"


@pytest.fixture(name="valid_token")
def valid_token_fixture(test_user_id: str) -> str:
    """
    Generate a valid JWT token for testing

    Token includes:
    - sub: user_id
    - exp: expiration (1 hour from now)
    - iat: issued at (now)
    """
    payload = {
        "sub": test_user_id,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")
    return token


@pytest.fixture(name="valid_token_user2")
def valid_token_user2_fixture(test_user_id_2: str) -> str:
    """Generate a valid JWT token for second test user"""
    payload = {
        "sub": test_user_id_2,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")
    return token


@pytest.fixture(name="expired_token")
def expired_token_fixture(test_user_id: str) -> str:
    """Generate an expired JWT token for testing auth failures"""
    payload = {
        "sub": test_user_id,
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        "iat": datetime.utcnow() - timedelta(hours=2)
    }
    token = jwt.encode(payload, settings.BETTER_AUTH_SECRET, algorithm="HS256")
    return token


@pytest.fixture(name="invalid_token")
def invalid_token_fixture() -> str:
    """Return an invalid JWT token for testing auth failures"""
    return "invalid.jwt.token"


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(valid_token: str) -> Dict[str, str]:
    """Return authorization headers with valid token"""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture(name="auth_headers_user2")
def auth_headers_user2_fixture(valid_token_user2: str) -> Dict[str, str]:
    """Return authorization headers for second test user"""
    return {"Authorization": f"Bearer {valid_token_user2}"}


# ============================================================
# MOCK OPENAI FIXTURES
# ============================================================

@pytest.fixture(name="mock_openai_response")
def mock_openai_response_fixture() -> Dict[str, Any]:
    """
    Mock OpenAI API response for testing agent orchestrator

    Returns a standard completion response without tool calls.
    """
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "I've added your task to the list!"
            },
            "finish_reason": "stop"
        }]
    }


@pytest.fixture(name="mock_openai_tool_call_response")
def mock_openai_tool_call_response_fixture() -> Dict[str, Any]:
    """
    Mock OpenAI API response with tool calls

    Simulates agent calling add_task tool.
    """
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "add_task",
                        "arguments": '{"title": "Buy groceries", "description": "Milk and bread"}'
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }]
    }


@pytest.fixture(name="mock_openai_client", autouse=True)
def mock_openai_client_fixture(mock_openai_response):
    """
    Mock OpenAI client to avoid hitting real API in tests

    Patches BOTH the module-level client AND the orchestrator's client attribute.
    Auto-applied to ALL tests to prevent accidental API calls.

    Tests can configure the mock by accessing the yielded mock_client in their
    setup or by using the fixture explicitly.
    """
    # Create mock client (sync, not async - OpenAI SDK uses sync client)
    mock_client = Mock()
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message.content = "Test response"
    mock_completion.choices[0].finish_reason = "stop"
    mock_completion.choices[0].message.tool_calls = None

    # Use regular Mock (not AsyncMock) because the OpenAI client is synchronous
    mock_client.chat.completions.create = Mock(return_value=mock_completion)

    # Patch both the module-level client and the orchestrator instance's client
    with patch("app.agent.orchestrator.client", mock_client):
        # Also patch the orchestrator singleton's client attribute
        from app.agent.orchestrator import orchestrator
        original_client = orchestrator.client
        orchestrator.client = mock_client

        yield mock_client

        # Restore original client
        orchestrator.client = original_client


# ============================================================
# TEST DATA FACTORIES
# ============================================================

@pytest.fixture(name="sample_task_data")
def sample_task_data_fixture() -> Dict[str, Any]:
    """Sample task data for creating tasks in tests"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "completed": False
    }


@pytest.fixture(name="sample_task")
def sample_task_fixture(session: Session, test_user_id: str) -> Task:
    """
    Create a sample task in the database

    Useful for tests that need existing tasks.
    """
    task = Task(
        user_id=test_user_id,
        title="Sample Task",
        description="Sample task for testing",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture(name="sample_conversation")
def sample_conversation_fixture(session: Session, test_user_id: str) -> Conversation:
    """
    Create a sample conversation in the database

    Useful for tests that need existing conversations.
    """
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@pytest.fixture(name="sample_message")
def sample_message_fixture(
    session: Session,
    test_user_id: str,
    sample_conversation: Conversation
) -> Message:
    """
    Create a sample message in the database

    Requires a conversation to exist first.
    """
    message = Message(
        conversation_id=sample_conversation.id,
        user_id=test_user_id,
        role="user",
        content="Hello, this is a test message"
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


# ============================================================
# CLEANUP FIXTURES
# ============================================================

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """
    Reset rate limit store before each test

    Prevents rate limit state from leaking between tests.
    """
    from app.middleware.auth import rate_limit_store
    rate_limit_store.clear()
    yield
    rate_limit_store.clear()


@pytest.fixture(autouse=True)
def clear_caches():
    """
    Clear any LRU caches before each test

    Ensures test isolation for cached functions.
    """
    from app.config import get_settings
    get_settings.cache_clear()
    yield


@pytest.fixture(autouse=True)
def reset_orchestrator_client():
    """
    Reset orchestrator client to use patched module-level client

    This ensures that when tests patch app.agent.orchestrator.client,
    the orchestrator instance picks up the patched client.
    """
    from app.agent import orchestrator as orch_module

    # Before test: sync orchestrator instance client with module-level client
    orch_module.orchestrator.client = orch_module.client

    yield

    # After test: restore sync
    orch_module.orchestrator.client = orch_module.client


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """
    Pytest configuration hook

    Runs before any tests are collected.
    """
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test (requires full stack)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
