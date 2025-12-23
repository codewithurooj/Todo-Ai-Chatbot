"""Message model for individual messages within conversations"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Message(SQLModel, table=True):
    """Individual message in a conversation (user or assistant)"""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    user_id: str = Field(index=True)  # JWT user ID (string from Better Auth)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
