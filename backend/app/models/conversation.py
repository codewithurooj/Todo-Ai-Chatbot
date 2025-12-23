"""Conversation model for chat sessions"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Conversation(SQLModel, table=True):
    """Chat conversation between user and AI assistant"""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # JWT user ID (string from Better Auth)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
