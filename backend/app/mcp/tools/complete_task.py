"""
complete_task MCP tool for marking tasks as completed
Follows MCP tool specification in contracts/mcp-tools.md
"""

from typing import Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.task import Task

# MCP Tool Schema for OpenAI Agent
COMPLETE_TASK_SCHEMA = {
    "name": "complete_task",
    "description": "Mark an existing task as completed. This is idempotent - completing an already-completed task will succeed.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier (enforces ownership)"
            },
            "task_id": {
                "type": "integer",
                "description": "ID of the task to mark as complete",
                "minimum": 1
            }
        },
        "required": ["user_id", "task_id"]
    }
}


def validate_task_id(task_id: int) -> tuple[bool, Optional[str]]:
    """
    Validate task_id parameter

    Args:
        task_id: Task ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(task_id, int):
        return False, "task_id must be an integer"

    if task_id < 1:
        return False, "task_id must be a positive integer"

    return True, None


async def complete_task_handler(
    user_id: str,
    task_id: int
) -> Dict[str, Any]:
    """
    Mark a task as completed

    This tool enforces user isolation by verifying task ownership before updating.
    It is idempotent - completing an already-completed task succeeds and returns the task.

    Args:
        user_id: User identifier (from JWT token)
        task_id: ID of task to complete

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
        - Uses WHERE clause with both task_id AND user_id for isolation

    Example:
        >>> result = await complete_task_handler(user_id="user123", task_id=456)
        >>> print(result)
        {
            "success": True,
            "task": {
                "id": 456,
                "user_id": "user123",
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": True,
                "created_at": "2025-12-21T10:30:00Z",
                "updated_at": "2025-12-21T15:45:00Z"
            }
        }
    """
    # Validate task_id
    is_valid, error_message = validate_task_id(task_id)
    if not is_valid:
        return {
            "success": False,
            "error": "ValidationError",
            "message": error_message
        }

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

            # Update task to completed
            db_task.completed = True
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
        print(f"Database error in complete_task: {str(e)}")
        return {
            "success": False,
            "error": "DatabaseError",
            "message": "Failed to complete task. Please try again."
        }
