"""MCP tool for creating tasks"""
from typing import Dict, Any, Optional
from sqlmodel import Session
from datetime import datetime

from app.models.task import Task, TaskCreate
from app.database import get_session
from app.middleware.error_handler import sanitize_input
import logging

logger = logging.getLogger(__name__)


async def add_task_handler(
    user_id: str,
    title: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new task for the authenticated user

    Args:
        user_id: User identifier (from JWT token)
        title: Task title (1-200 characters)
        description: Optional task description (max 1000 characters)

    Returns:
        {
            "success": True,
            "task": {
                "id": int,
                "user_id": str,
                "title": str,
                "description": str | null,
                "completed": False,
                "created_at": ISO datetime,
                "updated_at": ISO datetime
            }
        }

    Raises:
        ValueError: If validation fails
    """
    # Validate title
    if not title or not title.strip():
        return {
            "success": False,
            "error": "ValidationError",
            "message": "Title must not be empty"
        }

    title = title.strip()

    if len(title) > 200:
        return {
            "success": False,
            "error": "ValidationError",
            "message": "Title must be between 1 and 200 characters"
        }

    # Check for null bytes
    if '\x00' in title:
        return {
            "success": False,
            "error": "ValidationError",
            "message": "Title contains invalid characters"
        }

    # Validate description
    if description:
        description = description.strip()

        if len(description) > 1000:
            return {
                "success": False,
                "error": "ValidationError",
                "message": "Description must be 1000 characters or less"
            }

        if '\x00' in description:
            return {
                "success": False,
                "error": "ValidationError",
                "message": "Description contains invalid characters"
            }

        # Sanitize input to prevent XSS
        description = sanitize_input(description)
    else:
        description = None

    # Sanitize title
    title = sanitize_input(title)

    # Create task in database
    try:
        session_gen = get_session()
        session = next(session_gen)

        try:
            # Create task
            task_data = TaskCreate(
                title=title,
                description=description,
                completed=False
            )

            db_task = Task(
                **task_data.model_dump(),
                user_id=user_id
            )

            session.add(db_task)
            session.commit()
            session.refresh(db_task)

            logger.info(f"Created task {db_task.id} for user {user_id}")

            # Return success response
            return {
                "success": True,
                "task": {
                    "id": db_task.id,
                    "user_id": db_task.user_id,
                    "title": db_task.title,
                    "description": db_task.description,
                    "completed": db_task.completed,
                    "created_at": db_task.created_at.isoformat(),
                    "updated_at": db_task.updated_at.isoformat()
                }
            }

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Database error creating task: {str(e)}")
        return {
            "success": False,
            "error": "DatabaseError",
            "message": "Failed to create task"
        }


# MCP tool schema
ADD_TASK_SCHEMA = {
    "name": "add_task",
    "description": "Create a new task for the user. Use when user expresses a todo item, need, or intention (e.g., 'I need to buy groceries', 'remind me to call dentist').",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier (automatically provided)"
            },
            "title": {
                "type": "string",
                "description": "Task title (1-200 characters). Extract from user's message."
            },
            "description": {
                "type": "string",
                "description": "Optional task details (max 1000 characters)"
            }
        },
        "required": ["user_id", "title"]
    }
}


__all__ = ["add_task_handler", "ADD_TASK_SCHEMA"]
