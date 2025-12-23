"""Unit tests for AgentOrchestrator

Tests AI agent processing:
- Message formatting for OpenAI API
- Tool call processing
- Response generation
- Error handling (rate limits, authentication, connection errors)
- Context truncation
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from openai import RateLimitError, AuthenticationError, APIConnectionError, APIError

from app.agent.orchestrator import AgentOrchestrator, get_orchestrator


# ============================================================
# MESSAGE FORMATTING TESTS
# ============================================================

def test_format_messages_with_history():
    """Test formatting messages with conversation history"""
    orchestrator = AgentOrchestrator()

    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]

    current_message = "How are you?"

    formatted = orchestrator.format_messages(history, current_message)

    # Should have system prompt + history + current message
    assert len(formatted) == 4
    assert formatted[0]["role"] == "system"
    assert formatted[1] == history[0]
    assert formatted[2] == history[1]
    assert formatted[3]["role"] == "user"
    assert formatted[3]["content"] == "How are you?"


def test_format_messages_without_history():
    """Test formatting messages with empty history"""
    orchestrator = AgentOrchestrator()

    formatted = orchestrator.format_messages([], "Hello")

    # Should have system prompt + current message
    assert len(formatted) == 2
    assert formatted[0]["role"] == "system"
    assert formatted[1]["role"] == "user"
    assert formatted[1]["content"] == "Hello"


def test_format_messages_includes_system_prompt():
    """Test that formatted messages always include system prompt"""
    orchestrator = AgentOrchestrator()

    formatted = orchestrator.format_messages([], "Test")

    assert formatted[0]["role"] == "system"
    assert "task" in formatted[0]["content"].lower() or "assistant" in formatted[0]["content"].lower()


# ============================================================
# PROCESS MESSAGE TESTS (with mocked OpenAI)
# ============================================================

@pytest.mark.asyncio
async def test_process_message_success(test_user_id: str):
    """Test successful message processing"""
    orchestrator = AgentOrchestrator()

    # Mock OpenAI response
    mock_choice = Mock()
    mock_choice.message.content = "I can help you with that!"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    with patch.object(orchestrator.client.chat.completions, 'create', return_value=mock_response):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Can you help me?",
            conversation_history=[],
            tools=None
        )

    assert result["response"] == "I can help you with that!"
    assert result["finish_reason"] == "stop"
    assert "tool_calls" not in result or result.get("tool_calls") is None


@pytest.mark.asyncio
async def test_process_message_with_tool_calls(test_user_id: str):
    """Test message processing that triggers tool calls"""
    orchestrator = AgentOrchestrator()

    # Mock tool call
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "add_task"
    mock_tool_call.function.arguments = '{"title": "Buy groceries"}'

    mock_choice = Mock()
    mock_choice.message.content = ""
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.finish_reason = "tool_calls"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    tools = [{"type": "function", "function": {"name": "add_task"}}]

    with patch.object(orchestrator.client.chat.completions, 'create', return_value=mock_response):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Add task: buy groceries",
            conversation_history=[],
            tools=tools
        )

    assert result["finish_reason"] == "tool_calls"
    assert "tool_calls" in result
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["name"] == "add_task"
    assert result["tool_calls"][0]["id"] == "call_123"


@pytest.mark.asyncio
async def test_process_message_with_context(test_user_id: str):
    """Test processing message with conversation context"""
    orchestrator = AgentOrchestrator()

    history = [
        {"role": "user", "content": "My name is Alice"},
        {"role": "assistant", "content": "Nice to meet you, Alice!"},
    ]

    mock_choice = Mock()
    mock_choice.message.content = "Yes, Alice!"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    with patch.object(orchestrator.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Do you remember my name?",
            conversation_history=history,
            tools=None
        )

        # Verify that history was passed to OpenAI
        call_args = mock_create.call_args
        messages_arg = call_args.kwargs['messages']

        # Should include system, history, and current message
        assert len(messages_arg) >= 3
        assert any(msg["content"] == "My name is Alice" for msg in messages_arg)


# ============================================================
# ERROR HANDLING TESTS
# ============================================================

@pytest.mark.asyncio
async def test_process_message_rate_limit_error(test_user_id: str):
    """Test handling of OpenAI rate limit errors"""
    orchestrator = AgentOrchestrator()

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None)
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert "error" in result
    assert result["error"]["type"] == "RateLimitError"
    assert "high demand" in result["response"].lower()


@pytest.mark.asyncio
async def test_process_message_authentication_error(test_user_id: str):
    """Test handling of OpenAI authentication errors"""
    orchestrator = AgentOrchestrator()

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=AuthenticationError("Invalid API key", response=Mock(), body=None)
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert result["error"]["type"] == "AuthenticationError"
    assert "unavailable" in result["response"].lower() or "configuration" in result["response"].lower()


@pytest.mark.asyncio
async def test_process_message_connection_error(test_user_id: str):
    """Test handling of API connection errors"""
    orchestrator = AgentOrchestrator()

    # Create a mock APIConnectionError without message argument (constructor signature changed)
    mock_error = APIConnectionError(request=Mock())

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=mock_error
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert result["error"]["type"] == "ConnectionError"
    assert "connection" in result["response"].lower() or "connecting" in result["response"].lower()


@pytest.mark.asyncio
async def test_process_message_api_error_503(test_user_id: str):
    """Test handling of 503 Service Unavailable error"""
    orchestrator = AgentOrchestrator()

    mock_error = APIError("Service unavailable", request=Mock(), body=None)
    mock_error.status_code = 503

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=mock_error
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert result["error"]["type"] == "ServiceUnavailable"
    assert "unavailable" in result["response"].lower()


@pytest.mark.asyncio
async def test_process_message_generic_api_error(test_user_id: str):
    """Test handling of generic API errors"""
    orchestrator = AgentOrchestrator()

    mock_error = APIError("Unknown error", request=Mock(), body=None)
    mock_error.status_code = 500

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=mock_error
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert result["error"]["type"] == "APIError"


@pytest.mark.asyncio
async def test_process_message_unexpected_error(test_user_id: str):
    """Test handling of unexpected non-OpenAI errors"""
    orchestrator = AgentOrchestrator()

    with patch.object(
        orchestrator.client.chat.completions,
        'create',
        side_effect=Exception("Unexpected error")
    ):
        result = await orchestrator.process_message(
            user_id=test_user_id,
            message="Test message",
            conversation_history=[],
            tools=None
        )

    assert result["finish_reason"] == "error"
    assert result["error"]["type"] == "UnexpectedError"


# ============================================================
# HISTORY TRUNCATION TESTS
# ============================================================

def test_truncate_history_no_truncation_needed():
    """Test that short history is not truncated"""
    orchestrator = AgentOrchestrator()

    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]

    truncated = orchestrator.truncate_history(messages, max_tokens=1000)

    assert len(truncated) == 2
    assert truncated == messages


def test_truncate_history_removes_old_messages():
    """Test that truncation removes oldest messages first"""
    orchestrator = AgentOrchestrator()

    # Create messages that will exceed token limit
    messages = [
        {"role": "user", "content": "A" * 1000},
        {"role": "assistant", "content": "B" * 1000},
        {"role": "user", "content": "C" * 1000},
        {"role": "assistant", "content": "D" * 1000},
        {"role": "user", "content": "E" * 1000},
    ]

    # Set small token limit to force truncation
    truncated = orchestrator.truncate_history(messages, max_tokens=500)

    # Should keep only recent messages
    assert len(truncated) < len(messages)
    # Most recent message should be preserved
    assert truncated[-1]["content"] == "E" * 1000
    # Oldest messages should be removed
    assert not any(msg["content"] == "A" * 1000 for msg in truncated)


def test_truncate_history_empty_list():
    """Test truncating empty message list"""
    orchestrator = AgentOrchestrator()

    truncated = orchestrator.truncate_history([], max_tokens=1000)

    assert truncated == []


def test_truncate_history_preserves_order():
    """Test that truncation preserves chronological order"""
    orchestrator = AgentOrchestrator()

    messages = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
    ]

    truncated = orchestrator.truncate_history(messages, max_tokens=100)

    # Verify chronological order is maintained
    for i in range(len(truncated) - 1):
        current_idx = messages.index(truncated[i])
        next_idx = messages.index(truncated[i + 1])
        assert current_idx < next_idx


# ============================================================
# ORCHESTRATOR CONFIGURATION TESTS
# ============================================================

def test_orchestrator_initialization():
    """Test orchestrator initialization with defaults"""
    orchestrator = AgentOrchestrator()

    assert orchestrator.model == "gpt-4o-mini"  # From settings
    assert orchestrator.temperature == 0.7
    assert orchestrator.client is not None


def test_orchestrator_custom_model():
    """Test orchestrator with custom model"""
    orchestrator = AgentOrchestrator(model="gpt-4", temperature=0.5)

    assert orchestrator.model == "gpt-4"
    assert orchestrator.temperature == 0.5


def test_get_orchestrator_singleton():
    """Test that get_orchestrator returns same instance"""
    orchestrator1 = get_orchestrator()
    orchestrator2 = get_orchestrator()

    assert orchestrator1 is orchestrator2


# ============================================================
# INTEGRATION WITH TOOLS TESTS
# ============================================================

@pytest.mark.asyncio
async def test_process_message_passes_tools_to_api(test_user_id: str):
    """Test that tools are correctly passed to OpenAI API"""
    orchestrator = AgentOrchestrator()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_task",
                "description": "Add a task",
                "parameters": {}
            }
        }
    ]

    mock_choice = Mock()
    mock_choice.message.content = "Response"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    with patch.object(orchestrator.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        await orchestrator.process_message(
            user_id=test_user_id,
            message="Add a task",
            conversation_history=[],
            tools=tools
        )

        # Verify tools were passed to API
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["tools"] == tools
        assert call_kwargs["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_process_message_without_tools(test_user_id: str):
    """Test that tool_choice is not set when no tools provided"""
    orchestrator = AgentOrchestrator()

    mock_choice = Mock()
    mock_choice.message.content = "Response"
    mock_choice.message.tool_calls = None
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    with patch.object(orchestrator.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        await orchestrator.process_message(
            user_id=test_user_id,
            message="Hello",
            conversation_history=[],
            tools=None
        )

        # Verify tools and tool_choice are None
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["tools"] is None
        assert call_kwargs["tool_choice"] is None
