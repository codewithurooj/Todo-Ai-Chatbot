"""Integration tests for /api/{user_id}/chat endpoint

Tests the full chat flow:
- Creating conversations
- Processing messages
- Tool execution
- Message storage
- User isolation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlmodel import Session, select

from app.models.conversation import Conversation
from app.models.message import Message


# ============================================================
# SUCCESSFUL CHAT TESTS
# ============================================================

@pytest.mark.integration
def test_chat_create_new_conversation(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """Test creating a new conversation via chat endpoint"""
    # Configure mock OpenAI response
    mock_choice = Mock()
    mock_choice.message.content = "I can help you with that!"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_openai_client.chat.completions.create.return_value = mock_response

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Hello, can you help me?"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert "response" in data
    assert data["response"] == "I can help you with that!"

    # Verify conversation was created
    conversation = session.get(Conversation, data["conversation_id"])
    assert conversation is not None
    assert conversation.user_id == test_user_id


@pytest.mark.integration
def test_chat_use_existing_conversation(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    sample_conversation: Conversation
):
    """Test continuing an existing conversation"""
    with patch("app.agent.orchestrator.client") as mock_client:
        mock_choice = Mock()
        mock_choice.message.content = "Sure, I remember!"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            f"/api/{test_user_id}/chat",
            json={
                "message": "Do you remember our last conversation?",
                "conversation_id": sample_conversation.id
            },
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    # Should use the same conversation
    assert data["conversation_id"] == sample_conversation.id


@pytest.mark.integration
def test_chat_stores_messages(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """Test that chat endpoint stores both user and assistant messages"""
    # Configure mock OpenAI response
    mock_choice = Mock()
    mock_choice.message.content = "Response message"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_openai_client.chat.completions.create.return_value = mock_response

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "User message"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    conversation_id = data["conversation_id"]

    # Verify messages were stored
    statement = select(Message).where(Message.conversation_id == conversation_id)
    messages = session.exec(statement).all()

    assert len(messages) == 2

    # Check user message
    user_msg = next(msg for msg in messages if msg.role == "user")
    assert user_msg.content == "User message"

    # Check assistant message
    assistant_msg = next(msg for msg in messages if msg.role == "assistant")
    assert assistant_msg.content == "Response message"


@pytest.mark.integration
def test_chat_with_tool_calls(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """Test chat endpoint with tool execution"""
    # First response: tool call
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "add_task"
    mock_tool_call.function.arguments = '{"title": "Buy groceries", "description": "Milk and bread"}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # Second response: final response after tool execution
    mock_choice2 = Mock()
    mock_choice2.message.content = "I've added the task for you!"
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Add task: buy groceries - milk and bread"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should have tool_calls in response
    assert "tool_calls" in data
    assert len(data["tool_calls"]) > 0
    assert data["tool_calls"][0]["tool"] == "add_task"
    assert data["tool_calls"][0]["result"]["success"] is True


# ============================================================
# AUTHENTICATION & AUTHORIZATION TESTS
# ============================================================

@pytest.mark.integration
def test_chat_without_auth_token(client: TestClient, test_user_id: str):
    """Test that chat endpoint requires authentication"""
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Hello"}
        # No auth headers
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_chat_with_expired_token(
    client: TestClient,
    test_user_id: str,
    expired_token: str
):
    """Test that expired tokens are rejected"""
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_chat_with_invalid_token(
    client: TestClient,
    test_user_id: str,
    invalid_token: str
):
    """Test that invalid tokens are rejected"""
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {invalid_token}"}
    )

    assert response.status_code == 401


@pytest.mark.integration
def test_chat_user_id_mismatch(
    client: TestClient,
    test_user_id: str,
    test_user_id_2: str,
    auth_headers: dict
):
    """Test that user cannot chat with different user_id than token"""
    # auth_headers contains token for test_user_id
    # Try to chat as test_user_id_2
    response = client.post(
        f"/api/{test_user_id_2}/chat",
        json={"message": "Hello"},
        headers=auth_headers
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_chat_cannot_access_other_user_conversation(
    client: TestClient,
    test_user_id: str,
    test_user_id_2: str,
    auth_headers: dict,
    auth_headers_user2: dict,
    session: Session
):
    """Test that user cannot access another user's conversation"""
    # Create conversation for user 1
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Try to use that conversation as user 2
    with patch("app.agent.orchestrator.client") as mock_client:
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            f"/api/{test_user_id_2}/chat",
            json={
                "message": "Hello",
                "conversation_id": conversation.id
            },
            headers=auth_headers_user2
        )

    assert response.status_code == 404  # Conversation not found (for user 2)


# ============================================================
# VALIDATION TESTS
# ============================================================

@pytest.mark.integration
def test_chat_empty_message(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that empty messages are rejected"""
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "   "},  # Whitespace only
        headers=auth_headers
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_chat_message_too_long(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that messages exceeding 10,000 characters are rejected"""
    long_message = "A" * 10001

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": long_message},
        headers=auth_headers
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_chat_missing_message_field(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that message field is required"""
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={},  # Missing message field
        headers=auth_headers
    )

    # Backend validates before Pydantic, so it returns 400 instead of 422
    assert response.status_code == 400


@pytest.mark.integration
def test_chat_invalid_conversation_id(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test using non-existent conversation ID"""
    with patch("app.agent.orchestrator.client") as mock_client:
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            f"/api/{test_user_id}/chat",
            json={
                "message": "Hello",
                "conversation_id": 99999  # Non-existent
            },
            headers=auth_headers
        )

    assert response.status_code == 404


# ============================================================
# CONVERSATION CONTEXT TESTS
# ============================================================

@pytest.mark.integration
def test_chat_includes_conversation_history(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """Test that chat includes previous messages in context"""
    # Configure mock OpenAI response
    mock_choice = Mock()
    mock_choice.message.content = "Response"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_openai_client.chat.completions.create.return_value = mock_response

    # First message
    response1 = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "My name is Alice"},
        headers=auth_headers
    )
    conversation_id = response1.json()["conversation_id"]

    # Second message - should have first message in context
    response2 = client.post(
        f"/api/{test_user_id}/chat",
        json={
            "message": "What's my name?",
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )

    # Verify that OpenAI was called with history
    assert len(mock_openai_client.chat.completions.create.call_args_list) >= 2
    call_args = mock_openai_client.chat.completions.create.call_args_list[-1]
    messages = call_args.kwargs["messages"]

    # Should include the previous exchange
    message_contents = [msg["content"] for msg in messages]
    assert any("Alice" in content for content in message_contents)


# ============================================================
# ERROR HANDLING TESTS
# ============================================================

@pytest.mark.integration
def test_chat_handles_openai_errors_gracefully(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    mock_openai_client: Mock
):
    """Test that OpenAI errors return user-friendly messages"""
    from openai import RateLimitError

    # Configure mock to raise RateLimitError
    mock_openai_client.chat.completions.create.side_effect = RateLimitError(
        "Rate limit exceeded",
        response=Mock(),
        body=None
    )

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Hello"},
        headers=auth_headers
    )

    # Should still return 200 with error message in response
    assert response.status_code == 200
    data = response.json()
    assert "high demand" in data["response"].lower() or "try again" in data["response"].lower()


@pytest.mark.integration
def test_chat_response_schema(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that chat response matches expected schema"""
    with patch("app.agent.orchestrator.client") as mock_client:
        mock_choice = Mock()
        mock_choice.message.content = "Test response"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        response = client.post(
            f"/api/{test_user_id}/chat",
            json={"message": "Test message"},
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response schema
    assert "conversation_id" in data
    assert "response" in data
    assert "created_at" in data
    assert isinstance(data["conversation_id"], int)
    assert isinstance(data["response"], str)
