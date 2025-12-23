"""Conversation manager for handling chat history and persistence

Following patterns from conversation-manager skill for stateless architecture.
"""
from sqlmodel import Session, select
from typing import List, Dict, Optional
from datetime import datetime

from app.models.conversation import Conversation
from app.models.message import Message
from app.database import get_session
import logging

logger = logging.getLogger(__name__)

# Token counting (approximation if tiktoken not available)
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, using approximate token counting")


class ConversationManager:
    """
    Manages conversation lifecycle, message storage, and history retrieval

    Responsibilities:
    - Create new conversations
    - Store user and assistant messages
    - Retrieve conversation history with token-aware truncation
    - Enforce user isolation
    """

    def __init__(self):
        """Initialize conversation manager"""
        self.max_history_messages = 20  # Default limit for context window
        self.max_context_tokens = 4000  # Maximum tokens for conversation history

        # Initialize tokenizer if available
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
            except Exception:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Fallback
        else:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters for English text
            return len(text) // 4

    def truncate_history_by_tokens(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Truncate message history to fit within token budget

        Keeps most recent messages, drops oldest messages if needed.

        Args:
            messages: List of formatted messages
            max_tokens: Maximum tokens allowed (default: self.max_context_tokens)

        Returns:
            Truncated list of messages
        """
        max_tokens = max_tokens or self.max_context_tokens

        # Calculate total tokens
        total_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)

        # If within budget, return as-is
        if total_tokens <= max_tokens:
            logger.info(f"Message history within token budget: {total_tokens}/{max_tokens} tokens")
            return messages

        # Truncate from the beginning (oldest messages)
        logger.warning(f"Message history exceeds token budget: {total_tokens}/{max_tokens} tokens. Truncating...")

        truncated = []
        current_tokens = 0

        # Iterate from newest to oldest (reversed)
        for msg in reversed(messages):
            msg_tokens = self.count_tokens(msg["content"])

            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, msg)  # Insert at beginning to maintain order
                current_tokens += msg_tokens
            else:
                # Stop adding older messages
                break

        logger.info(f"Truncated history to {len(truncated)} messages ({current_tokens} tokens)")
        return truncated

    def create_conversation(
        self,
        user_id: str,
        session: Session
    ) -> Conversation:
        """
        Create a new conversation for a user

        Args:
            user_id: User identifier
            session: Database session

        Returns:
            Created conversation object
        """
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    def store_message(
        self,
        conversation_id: int,
        user_id: str,
        role: str,
        content: str,
        session: Session
    ) -> Message:
        """
        Store a message in a conversation

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for validation)
            role: Message role ("user" or "assistant")
            content: Message content
            session: Database session

        Returns:
            Stored message object

        Raises:
            ValueError: If conversation doesn't exist or doesn't belong to user
            ValueError: If role is invalid
        """
        # Validate conversation ownership
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.user_id != user_id:
            raise ValueError(f"Unauthorized access to conversation {conversation_id}")

        # Validate role
        if role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        # Validate content length
        if not content or len(content) > 10000:
            raise ValueError("Message content must be between 1 and 10,000 characters")

        # Create message
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content
        )

        session.add(message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)

        session.commit()
        session.refresh(message)

        logger.info(f"Stored {role} message in conversation {conversation_id}")
        return message

    def get_conversation_history(
        self,
        conversation_id: int,
        user_id: str,
        session: Session,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Retrieve conversation history formatted for AI agent

        Returns the most recent N messages in chronological order (oldest first).
        This ensures the AI agent sees the conversation flow correctly while
        respecting the context window limit.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for validation)
            session: Database session
            limit: Maximum number of messages to retrieve (default: 20)

        Returns:
            List of messages formatted as [{"role": "user", "content": "..."}, ...]
            Messages are in chronological order (oldest first)

        Raises:
            ValueError: If conversation doesn't exist or doesn't belong to user
        """
        # Validate conversation ownership
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.user_id != user_id:
            raise ValueError(f"Unauthorized access to conversation {conversation_id}")

        # Retrieve the MOST RECENT N messages (descending order)
        # then reverse to get chronological flow for the AI
        limit = limit or self.max_history_messages
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = session.exec(statement).all()

        # Reverse to chronological order (oldest first) for proper conversation flow
        messages = list(reversed(messages))

        # Format for AI agent
        formatted_messages = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]

        # Apply token-aware truncation
        formatted_messages = self.truncate_history_by_tokens(formatted_messages)

        logger.info(f"Retrieved {len(formatted_messages)} most recent messages from conversation {conversation_id}")
        return formatted_messages

    def list_conversations(
        self,
        user_id: str,
        session: Session,
        limit: int = 50,
        sort_by: str = "updated_at",
        order: str = "desc"
    ) -> List[Conversation]:
        """
        List all conversations for a user

        Args:
            user_id: User ID
            session: Database session
            limit: Maximum conversations to return
            sort_by: Sort field ("created_at" or "updated_at")
            order: Sort order ("asc" or "desc")

        Returns:
            List of conversation objects
        """
        statement = select(Conversation).where(Conversation.user_id == user_id)

        # Apply sorting
        if sort_by == "created_at":
            statement = statement.order_by(
                Conversation.created_at.desc() if order == "desc" else Conversation.created_at.asc()
            )
        else:  # default to updated_at
            statement = statement.order_by(
                Conversation.updated_at.desc() if order == "desc" else Conversation.updated_at.asc()
            )

        statement = statement.limit(limit)

        conversations = session.exec(statement).all()

        logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
        return conversations

    def get_conversation(
        self,
        conversation_id: int,
        user_id: str,
        session: Session
    ) -> Conversation:
        """
        Get a specific conversation with ownership validation

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for validation)
            session: Database session

        Returns:
            Conversation object

        Raises:
            ValueError: If conversation doesn't exist or doesn't belong to user
        """
        conversation = session.get(Conversation, conversation_id)

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if conversation.user_id != user_id:
            raise ValueError(f"Unauthorized access to conversation {conversation_id}")

        return conversation

    def delete_conversation(
        self,
        conversation_id: int,
        user_id: str,
        session: Session
    ) -> Dict[str, int]:
        """
        Delete a conversation and all its messages

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for validation)
            session: Database session

        Returns:
            {"deleted_conversation_id": int, "deleted_message_count": int}

        Raises:
            ValueError: If conversation doesn't exist or doesn't belong to user
        """
        # Validate ownership
        conversation = self.get_conversation(conversation_id, user_id, session)

        # Count messages before deletion
        message_count_stmt = select(Message).where(Message.conversation_id == conversation_id)
        messages = session.exec(message_count_stmt).all()
        message_count = len(messages)

        # Delete messages (will cascade if foreign key is set, but being explicit)
        for message in messages:
            session.delete(message)

        # Delete conversation
        session.delete(conversation)
        session.commit()

        logger.info(f"Deleted conversation {conversation_id} with {message_count} messages")
        return {
            "deleted_conversation_id": conversation_id,
            "deleted_message_count": message_count
        }


# Global conversation manager instance
conversation_manager = ConversationManager()


def get_conversation_manager() -> ConversationManager:
    """
    Get the global conversation manager instance

    Returns:
        ConversationManager: The conversation manager
    """
    return conversation_manager


__all__ = ["ConversationManager", "conversation_manager", "get_conversation_manager"]
