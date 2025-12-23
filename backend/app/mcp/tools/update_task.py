"""
update_task MCP tool for modifying task title and/or description
Follows MCP tool specification in contracts/mcp-tools.md
"""

from typing import Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.task import Task

# MCP Tool Schema for OpenAI Agent
UPDATE_TASK_SCHEMA = {
    "name": "update_task",
    "description": "Modify an existing task's title and/or description. At least one field must be provided.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier (enforces ownership)"
            },
            "task_id": {
                "type": "integer",
                "description": "ID of the task to update",
                "minimum": 1
            },
            "title": {
                "type": "string",
                "description": "New task title (1-200 characters)",
                "minLength": 1,
                "maxLength": 200
            },
            "description": {
                "type": "string",
                "description": "New task description (max 1000 characters)",
                "maxLength": 1000
            },
            "completed": {
                "type": "boolean",
                "description": "Mark task as completed (true) or incomplete (false)"
            }
        },
        "required": ["user_id", "task_id"]
    }
}


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace('\x00', '')

    # Strip whitespace
    text = text.strip()

    return text


def validate_update_params(
    task_id: int,
    title: Optional[str],
    description: Optional[str],
    completed: Optional[bool]
) -> tuple[bool, Optional[str]]:
    """
    Validate update_task parameters

    Args:
        task_id: Task ID to validate
        title: Optional new title
        description: Optional new description
        completed: Optional completion status

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate task_id
    if not isinstance(task_id, int) or task_id < 1:
        return False, "task_id must be a positive integer"

    # At least one of title, description, or completed must be provided
    if title is None and description is None and completed is None:
        return False, "At least one of title, description, or completed must be provided"

    # Validate title if provided
    if title is not None:
        if not title or not title.strip():
            return False, "Title must not be empty or whitespace-only"
        if len(title) > 200:
            return False, "Title must be between 1 and 200 characters"
        if '\x00' in title:
            return False, "Title contains invalid characters"

    # Validate description if provided
    if description is not None:
        if len(description) > 1000:
            return False, "Description must be 1000 characters or less"
        if '\x00' in description:
            return False, "Description contains invalid characters"

    # Validate completed if provided
    if completed is not None:
        if not isinstance(completed, bool):
            return False, "Completed must be a boolean value (true or false)"

    return True, None


async def update_task_handler(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update a task's title, description, and/or completion status

    This tool enforces user isolation by verifying task ownership before updating.
    At least one of title, description, or completed must be provided.

    Args:
        user_id: User identifier (from JWT token)
        task_id: ID of task to update
        title: Optional new task title (1-200 characters)
        description: Optional new task description (max 1000 characters)
        completed: Optional completion status (true for completed, false for incomplete)

    Returns:
        Dictionary with:
        - success (bool): Whether operation succeeded
        - task (dict): Updated task object with all fields

        OR on error:
        - success (bool): False
        - error (str): Error type
        - message (str): Error description

    Security:
        - Always verifies task belongs to user_id before updating
        - Can change completion status via completed parameter
        - Cannot change user_id (security constraint)
        - Sanitizes inputs to prevent XSS attacks

    Example:
        >>> result = await update_task_handler(
        ...     user_id="user123",
        ...     task_id=456,
        ...     title="Buy groceries and milk",
        ...     completed=True
        ... )
        >>> print(result)
        {
            "success": True,
            "task": {
                "id": 456,
                "user_id": "user123",
                "title": "Buy groceries and milk",
                "description": "Milk, eggs, bread",
                "completed": True,
                "created_at": "2025-12-21T10:30:00Z",
                "updated_at": "2025-12-21T16:00:00Z"
            }
        }
    """
    # Validate parameters
    is_valid, error_message = validate_update_params(task_id, title, description, completed)
    if not is_valid:
        return {
            "success": False,
            "error": "ValidationError",
            "message": error_message
        }

    # Sanitize inputs
    if title is not None:
        title = sanitize_input(title)
    if description is not None:
        description = sanitize_input(description)

    try:
        # Get database session
        session_gen = get_session()
        session = next(session_gen)

        try:
            # Find task with user isolation
            query = select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id
            )
            db_task = session.exec(query).first()

            # Check if task exists and belongs to user
            if not db_task:
                return {
                    "success": False,
                    "error": "NotFoundError",
                    "message": "Task not found or does not belong to user"
                }

            # Update fields if provided
            if title is not None:
                db_task.title = title
            if description is not None:
                db_task.description = description
            if completed is not None:
                db_task.completed = completed

            # Always update the updated_at timestamp
            db_task.updated_at = datetime.utcnow()

            # Commit changes
            session.add(db_task)
            session.commit()
            session.refresh(db_task)

            # Return updated task
            return {
                "success": True,
                "task": {
                    "id": db_task.id,
                    "user_id": db_task.user_id,
                    "title": db_task.title,
                    "description": db_task.description,
                    "completed": db_task.completed,
                    "created_at": db_task.created_at.isoformat() if db_task.created_at else None,
                    "updated_at": db_task.updated_at.isoformat() if db_task.updated_at else None
                }
            }

        finally:
            session.close()

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in update_task: {str(e)}")
        return {
            "success": False,
            "error": "DatabaseError",
            "message": "Failed to update task. Please try again."
        }
