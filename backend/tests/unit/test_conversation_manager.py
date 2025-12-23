"""Unit tests for ConversationManager

Tests conversation history management:
- Creating conversations
- Storing messages
- Retrieving conversation history with token-aware truncation
- User isolation and security
- Conversation deletion
"""
import pytest
from sqlmodel import Session, select
from datetime import datetime

from app.agent.conversation_manager import ConversationManager, get_conversation_manager
from app.models.conversation import Conversation
from app.models.message import Message


# ============================================================
# CONVERSATION CREATION TESTS
# ============================================================

def test_create_conversation(session: Session, test_user_id: str):
    """Test creating a new conversation"""
    manager = ConversationManager()

    conversation = manager.create_conversation(
        user_id=test_user_id,
        session=session
    )

    assert conversation.id is not None
    assert conversation.user_id == test_user_id
    assert isinstance(conversation.created_at, datetime)


def test_create_multiple_conversations(session: Session, test_user_id: str):
    """Test creating multiple conversations for same user"""
    manager = ConversationManager()

    conv1 = manager.create_conversation(test_user_id, session)
    conv2 = manager.create_conversation(test_user_id, session)

    assert conv1.id != conv2.id
    assert conv1.user_id == test_user_id
    assert conv2.user_id == test_user_id


# ============================================================
# MESSAGE STORAGE TESTS
# ============================================================

def test_store_user_message(session: Session, test_user_id: str):
    """Test storing a user message"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    message = manager.store_message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content="Hello, AI assistant!",
        session=session
    )

    assert message.id is not None
    assert message.conversation_id == conversation.id
    assert message.user_id == test_user_id
    assert message.role == "user"
    assert message.content == "Hello, AI assistant!"


def test_store_assistant_message(session: Session, test_user_id: str):
    """Test storing an assistant message"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    message = manager.store_message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="assistant",
        content="Hello! How can I help you today?",
        session=session
    )

    assert message.role == "assistant"
    assert message.content == "Hello! How can I help you today?"


def test_store_message_updates_conversation_timestamp(session: Session, test_user_id: str):
    """Test that storing a message updates conversation.updated_at"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)
    original_updated_at = conversation.updated_at

    import time
    time.sleep(0.1)  # Ensure timestamp difference

    manager.store_message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content="New message",
        session=session
    )

    # Refresh conversation to get updated timestamp
    session.refresh(conversation)
    assert conversation.updated_at > original_updated_at


def test_store_message_invalid_conversation(session: Session, test_user_id: str):
    """Test storing message with non-existent conversation ID"""
    manager = ConversationManager()

    with pytest.raises(ValueError, match="not found"):
        manager.store_message(
            conversation_id=99999,
            user_id=test_user_id,
            role="user",
            content="Message to nowhere",
            session=session
        )


def test_store_message_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that user cannot store message in another user's conversation"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    with pytest.raises(ValueError, match="Unauthorized"):
        manager.store_message(
            conversation_id=conversation.id,
            user_id=test_user_id_2,  # Different user!
            role="user",
            content="Unauthorized message",
            session=session
        )


def test_store_message_invalid_role(session: Session, test_user_id: str):
    """Test storing message with invalid role"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    with pytest.raises(ValueError, match="Invalid role"):
        manager.store_message(
            conversation_id=conversation.id,
            user_id=test_user_id,
            role="system",  # Invalid role (only "user" or "assistant" allowed)
            content="System message",
            session=session
        )


def test_store_message_empty_content(session: Session, test_user_id: str):
    """Test storing message with empty content"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    with pytest.raises(ValueError, match="content must be between"):
        manager.store_message(
            conversation_id=conversation.id,
            user_id=test_user_id,
            role="user",
            content="",  # Empty content
            session=session
        )


def test_store_message_exceeds_max_length(session: Session, test_user_id: str):
    """Test storing message exceeding 10,000 character limit"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    long_content = "A" * 10001  # Exceeds 10,000 limit

    with pytest.raises(ValueError, match="10,000 characters"):
        manager.store_message(
            conversation_id=conversation.id,
            user_id=test_user_id,
            role="user",
            content=long_content,
            session=session
        )


# ============================================================
# CONVERSATION HISTORY RETRIEVAL TESTS
# ============================================================

def test_get_conversation_history_empty(session: Session, test_user_id: str):
    """Test retrieving history from conversation with no messages"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    history = manager.get_conversation_history(
        conversation_id=conversation.id,
        user_id=test_user_id,
        session=session
    )

    assert history == []


def test_get_conversation_history_single_message(session: Session, test_user_id: str):
    """Test retrieving history with one message"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    manager.store_message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content="Hello",
        session=session
    )

    history = manager.get_conversation_history(
        conversation_id=conversation.id,
        user_id=test_user_id,
        session=session
    )

    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"


def test_get_conversation_history_multiple_messages(session: Session, test_user_id: str):
    """Test retrieving history with multiple messages in chronological order"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    # Store messages in sequence
    manager.store_message(conversation.id, test_user_id, "user", "Hi", session)
    manager.store_message(conversation.id, test_user_id, "assistant", "Hello!", session)
    manager.store_message(conversation.id, test_user_id, "user", "How are you?", session)

    history = manager.get_conversation_history(
        conversation_id=conversation.id,
        user_id=test_user_id,
        session=session
    )

    assert len(history) == 3
    # Verify chronological order (oldest first)
    assert history[0]["content"] == "Hi"
    assert history[1]["content"] == "Hello!"
    assert history[2]["content"] == "How are you?"


def test_get_conversation_history_respects_limit(session: Session, test_user_id: str):
    """Test that history retrieval respects message limit"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    # Create 25 messages
    for i in range(25):
        role = "user" if i % 2 == 0 else "assistant"
        manager.store_message(
            conversation.id,
            test_user_id,
            role,
            f"Message {i}",
            session
        )

    # Get history with limit of 10
    history = manager.get_conversation_history(
        conversation_id=conversation.id,
        user_id=test_user_id,
        session=session,
        limit=10
    )

    # Should return 10 most recent messages
    assert len(history) == 10
    # Should be the last 10 messages (15-24)
    assert history[-1]["content"] == "Message 24"


def test_get_conversation_history_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that user cannot access another user's conversation history"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    manager.store_message(conversation.id, test_user_id, "user", "Private message", session)

    # Try to access with different user
    with pytest.raises(ValueError, match="Unauthorized"):
        manager.get_conversation_history(
            conversation_id=conversation.id,
            user_id=test_user_id_2,
            session=session
        )


def test_get_conversation_history_nonexistent(session: Session, test_user_id: str):
    """Test retrieving history from non-existent conversation"""
    manager = ConversationManager()

    with pytest.raises(ValueError, match="not found"):
        manager.get_conversation_history(
            conversation_id=99999,
            user_id=test_user_id,
            session=session
        )


# ============================================================
# TOKEN TRUNCATION TESTS
# ============================================================

def test_count_tokens_approximation():
    """Test token counting (approximate method)"""
    manager = ConversationManager()

    # Short text
    text1 = "Hello"
    tokens1 = manager.count_tokens(text1)
    assert tokens1 > 0

    # Longer text should have more tokens
    text2 = "Hello, this is a much longer message with many more words."
    tokens2 = manager.count_tokens(text2)
    assert tokens2 > tokens1


def test_truncate_history_by_tokens_no_truncation():
    """Test that short history is not truncated"""
    manager = ConversationManager()

    messages = [
        {"role": "user", "content": "Short message"},
        {"role": "assistant", "content": "Short response"}
    ]

    truncated = manager.truncate_history_by_tokens(messages, max_tokens=1000)

    assert len(truncated) == 2
    assert truncated == messages


def test_truncate_history_by_tokens_removes_oldest():
    """Test that truncation removes oldest messages"""
    manager = ConversationManager()

    # Create messages that exceed token budget
    messages = [
        {"role": "user", "content": "A" * 1000},
        {"role": "assistant", "content": "B" * 1000},
        {"role": "user", "content": "C" * 1000},
        {"role": "assistant", "content": "D" * 1000},
        {"role": "user", "content": "E" * 1000},
    ]

    # Set low token limit to force truncation
    truncated = manager.truncate_history_by_tokens(messages, max_tokens=500)

    # Should keep only most recent messages
    assert len(truncated) < len(messages)
    # Most recent message should be preserved
    assert truncated[-1]["content"] == "E" * 1000


# ============================================================
# CONVERSATION MANAGEMENT TESTS
# ============================================================

def test_list_conversations(session: Session, test_user_id: str):
    """Test listing all conversations for a user"""
    manager = ConversationManager()

    # Create multiple conversations
    conv1 = manager.create_conversation(test_user_id, session)
    conv2 = manager.create_conversation(test_user_id, session)
    conv3 = manager.create_conversation(test_user_id, session)

    conversations = manager.list_conversations(
        user_id=test_user_id,
        session=session
    )

    assert len(conversations) == 3
    conv_ids = {conv.id for conv in conversations}
    assert conv1.id in conv_ids
    assert conv2.id in conv_ids
    assert conv3.id in conv_ids


def test_list_conversations_user_isolation(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that list_conversations only returns user's own conversations"""
    manager = ConversationManager()

    # Create conversations for both users
    manager.create_conversation(test_user_id, session)
    manager.create_conversation(test_user_id, session)
    manager.create_conversation(test_user_id_2, session)

    # List user 1's conversations
    user1_convs = manager.list_conversations(test_user_id, session)

    assert len(user1_convs) == 2
    assert all(conv.user_id == test_user_id for conv in user1_convs)


def test_get_conversation(session: Session, test_user_id: str):
    """Test retrieving a specific conversation"""
    manager = ConversationManager()
    created_conv = manager.create_conversation(test_user_id, session)

    retrieved_conv = manager.get_conversation(
        conversation_id=created_conv.id,
        user_id=test_user_id,
        session=session
    )

    assert retrieved_conv.id == created_conv.id
    assert retrieved_conv.user_id == test_user_id


def test_get_conversation_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that user cannot get another user's conversation"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    with pytest.raises(ValueError, match="Unauthorized"):
        manager.get_conversation(
            conversation_id=conversation.id,
            user_id=test_user_id_2,
            session=session
        )


def test_delete_conversation(session: Session, test_user_id: str):
    """Test deleting a conversation and its messages"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    # Add some messages
    manager.store_message(conversation.id, test_user_id, "user", "Message 1", session)
    manager.store_message(conversation.id, test_user_id, "assistant", "Response 1", session)

    # Delete conversation
    result = manager.delete_conversation(
        conversation_id=conversation.id,
        user_id=test_user_id,
        session=session
    )

    assert result["deleted_conversation_id"] == conversation.id
    assert result["deleted_message_count"] == 2

    # Verify conversation is deleted
    statement = select(Conversation).where(Conversation.id == conversation.id)
    deleted_conv = session.exec(statement).first()
    assert deleted_conv is None

    # Verify messages are deleted
    statement = select(Message).where(Message.conversation_id == conversation.id)
    messages = session.exec(statement).all()
    assert len(messages) == 0


def test_delete_conversation_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that user cannot delete another user's conversation"""
    manager = ConversationManager()
    conversation = manager.create_conversation(test_user_id, session)

    with pytest.raises(ValueError, match="Unauthorized"):
        manager.delete_conversation(
            conversation_id=conversation.id,
            user_id=test_user_id_2,
            session=session
        )


# ============================================================
# GLOBAL INSTANCE TESTS
# ============================================================

def test_get_conversation_manager_singleton():
    """Test that get_conversation_manager returns same instance"""
    manager1 = get_conversation_manager()
    manager2 = get_conversation_manager()

    assert manager1 is manager2
