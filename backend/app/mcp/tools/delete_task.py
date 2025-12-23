"""
delete_task MCP tool for permanently removing tasks
Follows MCP tool specification in contracts/mcp-tools.md
"""

from typing import Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.task import Task

# MCP Tool Schema for OpenAI Agent
DELETE_TASK_SCHEMA = {
    "name": "delete_task",
    "description": "Permanently remove a task from the user's task list. This action cannot be undone.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier (enforces ownership)"
            },
            "task_id": {
                "type": "integer",
                "description": "ID of the task to delete",
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


async def delete_task_handler(
    user_id: str,
    task_id: int
) -> Dict[str, Any]:
    """
    Permanently delete a task

    This tool enforces user isolation by verifying task ownership before deletion.
    Performs a hard delete (permanent removal from database).

    Args:
        user_id: User identifier (from JWT token)
        task_id: ID of task to delete

    Returns:
        Dictionary with:
        - success (bool): Whether operation succeeded
        - deleted_task_id (int): ID of the deleted task
        - message (str): Confirmation message

        OR on error:
        - success (bool): False
        - error (str): Error type
        - message (str): Error description

    Security:
        - Always verifies task belongs to user_id before deleting
        - Hard delete (permanent removal from database)
        - Uses WHERE clause with both task_id AND user_id for isolation

    Example:
        >>> result = await delete_task_handler(user_id="user123", task_id=456)
        >>> print(result)
        {
            "success": True,
            "deleted_task_id": 456,
            "message": "Task deleted successfully"
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

            # Delete the task
            session.delete(db_task)
            session.commit()

            # Return success response
            return {
                "success": True,
                "deleted_task_id": task_id,
                "message": "Task deleted successfully"
            }

        finally:
            session.close()

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in delete_task: {str(e)}")
        return {
            "success": False,
            "error": "DatabaseError",
            "message": "Failed to delete task. Please try again."
        }
