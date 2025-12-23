"""Conversation endpoints for retrieving chat history"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_session
from app.middleware.auth import get_current_user_id
from app.agent.conversation_manager import get_conversation_manager
from app.models.conversation import Conversation
from app.models.message import Message
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    """Conversation metadata response"""
    id: int
    user_id: str
    created_at: str
    updated_at: str
    message_count: Optional[int] = None


class MessageResponse(BaseModel):
    """Message response"""
    id: int
    conversation_id: int
    user_id: str
    role: str
    content: str
    created_at: str


class ConversationWithMessagesResponse(BaseModel):
    """Conversation with messages response"""
    id: int
    user_id: str
    created_at: str
    updated_at: str
    messages: List[MessageResponse]


@router.get("", response_model=List[ConversationResponse], status_code=status.HTTP_200_OK)
async def list_conversations(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=100, description="Maximum conversations to return"),
    sort_by: str = Query("updated_at", regex="^(created_at|updated_at)$", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List all conversations for the authenticated user

    Returns conversation metadata with optional message count.
    Conversations are sorted by updated_at (most recent first) by default.

    Args:
        user_id: User ID from path
        current_user_id: Authenticated user ID from JWT
        session: Database session
        limit: Maximum conversations to return (1-100)
        sort_by: Sort field ("created_at" or "updated_at")
        order: Sort order ("asc" or "desc")

    Returns:
        List of conversation objects with metadata

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    conversation_manager = get_conversation_manager()

    try:
        # Get conversations
        conversations = conversation_manager.list_conversations(
            user_id=user_id,
            session=session,
            limit=limit,
            sort_by=sort_by,
            order=order
        )

        # Format response
        response = [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                created_at=conv.created_at.isoformat() if conv.created_at else None,
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None
            )
            for conv in conversations
        ]

        return response

    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def get_conversation_messages(
    user_id: str,
    conversation_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    limit: int = Query(100, ge=1, le=500, description="Maximum messages to return")
):
    """
    Get messages for a specific conversation

    Returns messages in chronological order (oldest first).

    Args:
        user_id: User ID from path
        conversation_id: Conversation ID
        current_user_id: Authenticated user ID from JWT
        session: Database session
        limit: Maximum messages to return (1-500)

    Returns:
        List of messages in chronological order

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If conversation doesn't exist or doesn't belong to user
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    conversation_manager = get_conversation_manager()

    try:
        # Validate conversation ownership
        conversation_manager.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            session=session
        )

        # Get messages
        messages_dict = conversation_manager.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            session=session,
            limit=limit
        )

        # Get full message objects with IDs and timestamps
        from sqlmodel import select
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        db_messages = session.exec(statement).all()
        db_messages = list(reversed(db_messages))  # Chronological order

        # Format response
        response = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                user_id=msg.user_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat() if msg.created_at else None
            )
            for msg in db_messages
        ]

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    user_id: str,
    conversation_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Delete a conversation and all its messages

    This is a permanent delete operation. All messages in the conversation
    will also be deleted.

    Args:
        user_id: User ID from path
        conversation_id: Conversation ID to delete
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        Deletion confirmation with counts

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If conversation doesn't exist or doesn't belong to user
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    conversation_manager = get_conversation_manager()

    try:
        result = conversation_manager.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            session=session
        )

        return {
            "success": True,
            "deleted_conversation_id": result["deleted_conversation_id"],
            "deleted_message_count": result["deleted_message_count"],
            "message": "Conversation and messages deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


__all__ = ["router"]
