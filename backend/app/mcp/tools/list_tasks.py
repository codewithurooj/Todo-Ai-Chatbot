"""
list_tasks MCP tool for retrieving user's tasks with filtering
Follows MCP tool specification in contracts/mcp-tools.md
"""

from typing import Dict, Any, List, Optional
from sqlmodel import Session, select, func
from datetime import datetime

from app.database import get_session
from app.models.task import Task

# MCP Tool Schema for OpenAI Agent
LIST_TASKS_SCHEMA = {
    "name": "list_tasks",
    "description": "Retrieve user's tasks with optional filtering by completion status. Returns tasks in reverse chronological order (newest first).",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier (enforces ownership)"
            },
            "filter": {
                "type": "string",
                "enum": ["all", "pending", "completed"],
                "description": "Task filter: 'all' for all tasks, 'pending' for incomplete tasks, 'completed' for completed tasks",
                "default": "pending"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of tasks to return (1-200)",
                "minimum": 1,
                "maximum": 200,
                "default": 50
            },
            "offset": {
                "type": "integer",
                "description": "Pagination offset (number of tasks to skip)",
                "minimum": 0,
                "default": 0
            }
        },
        "required": ["user_id"]
    }
}


def validate_list_params(
    filter_value: str,
    limit: int,
    offset: int
) -> tuple[bool, Optional[str]]:
    """
    Validate list_tasks parameters

    Args:
        filter_value: Task filter ("all", "pending", "completed")
        limit: Maximum number of tasks to return
        offset: Pagination offset

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate filter
    allowed_filters = ["all", "pending", "completed"]
    if filter_value not in allowed_filters:
        return False, f"Filter must be one of: {', '.join(allowed_filters)}"

    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        return False, "Limit must be an integer between 1 and 200"

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        return False, "Offset must be a non-negative integer"

    return True, None


async def list_tasks_handler(
    user_id: str,
    filter: str = "all",
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieve user's tasks with optional filtering

    This tool enforces user isolation by always filtering tasks by user_id.
    Returns tasks in reverse chronological order (newest first).

    Args:
        user_id: User identifier (from JWT token)
        filter: Task filter ("all", "pending", "completed")
        limit: Maximum number of tasks to return (1-200)
        offset: Pagination offset

    Returns:
        Dictionary with:
        - success (bool): Whether operation succeeded
        - tasks (list): List of task objects
        - total (int): Total number of tasks matching filter
        - has_more (bool): Whether more tasks exist beyond current page

        OR on error:
        - success (bool): False
        - error (str): Error type
        - message (str): Error description

    Security:
        - Always filters by user_id to enforce user isolation
        - Never returns tasks belonging to other users
        - Limits maximum page size to prevent resource exhaustion

    Example:
        >>> result = await list_tasks_handler(user_id="user123", filter="pending", limit=10)
        >>> print(result)
        {
            "success": True,
            "tasks": [
                {
                    "id": 1,
                    "user_id": "user123",
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "completed": False,
                    "created_at": "2025-12-21T10:30:00Z",
                    "updated_at": "2025-12-21T10:30:00Z"
                }
            ],
            "total": 1,
            "has_more": False
        }
    """
    # Validate parameters
    is_valid, error_message = validate_list_params(filter, limit, offset)
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
            # Build base query with user isolation
            query = select(Task).where(Task.user_id == user_id)

            # Apply filter based on completion status
            if filter == "pending":
                query = query.where(Task.completed == False)
            elif filter == "completed":
                query = query.where(Task.completed == True)
            # "all" doesn't add additional filter

            # Get total count (before pagination)
            count_query = select(func.count()).select_from(Task).where(Task.user_id == user_id)
            if filter == "pending":
                count_query = count_query.where(Task.completed == False)
            elif filter == "completed":
                count_query = count_query.where(Task.completed == True)

            total = session.exec(count_query).one()

            # Apply ordering (newest first)
            query = query.order_by(Task.created_at.desc())

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query
            db_tasks = session.exec(query).all()

            # Calculate has_more
            has_more = (offset + len(db_tasks)) < total

            # Convert tasks to dictionaries
            tasks = []
            for task in db_tasks:
                tasks.append({
                    "id": task.id,
                    "user_id": task.user_id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                })

            return {
                "success": True,
                "tasks": tasks,
                "total": total,
                "has_more": has_more
            }

        finally:
            session.close()

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in list_tasks: {str(e)}")
        return {
            "success": False,
            "error": "DatabaseError",
            "message": "Failed to retrieve tasks. Please try again."
        }
