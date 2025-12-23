"""Unit tests for MCP tool handlers

Tests all 5 MCP tools:
- add_task: Create new tasks
- list_tasks: Retrieve user tasks
- complete_task: Mark tasks as complete
- delete_task: Remove tasks
- update_task: Modify task fields
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import Session

from app.mcp.tools.add_task import add_task_handler
from app.mcp.tools.list_tasks import list_tasks_handler
from app.mcp.tools.complete_task import complete_task_handler
from app.mcp.tools.delete_task import delete_task_handler
from app.mcp.tools.update_task import update_task_handler
from app.models.task import Task


# ============================================================
# ADD_TASK TESTS
# ============================================================

@pytest.mark.asyncio
async def test_add_task_success(test_user_id: str):
    """Test successfully creating a task"""
    result = await add_task_handler(
        user_id=test_user_id,
        title="Buy groceries",
        description="Milk and bread"
    )

    assert result["success"] is True
    assert "task" in result
    assert result["task"]["title"] == "Buy groceries"
    assert result["task"]["description"] == "Milk and bread"
    assert result["task"]["completed"] is False
    assert result["task"]["user_id"] == test_user_id


@pytest.mark.asyncio
async def test_add_task_without_description(test_user_id: str):
    """Test creating a task without optional description"""
    result = await add_task_handler(
        user_id=test_user_id,
        title="Call dentist"
    )

    assert result["success"] is True
    assert result["task"]["title"] == "Call dentist"
    assert result["task"]["description"] is None


@pytest.mark.asyncio
async def test_add_task_empty_title(test_user_id: str):
    """Test validation error for empty title"""
    result = await add_task_handler(
        user_id=test_user_id,
        title="   "  # Whitespace only
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"
    assert "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_add_task_title_too_long(test_user_id: str):
    """Test validation error for title exceeding 200 characters"""
    long_title = "A" * 201

    result = await add_task_handler(
        user_id=test_user_id,
        title=long_title
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"
    assert "200 characters" in result["message"]


@pytest.mark.asyncio
async def test_add_task_description_too_long(test_user_id: str):
    """Test validation error for description exceeding 1000 characters"""
    long_description = "B" * 1001

    result = await add_task_handler(
        user_id=test_user_id,
        title="Valid title",
        description=long_description
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"
    assert "1000 characters" in result["message"]


@pytest.mark.asyncio
async def test_add_task_null_bytes(test_user_id: str):
    """Test validation error for null bytes in title"""
    result = await add_task_handler(
        user_id=test_user_id,
        title="Task with \x00 null byte"
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"
    assert "invalid characters" in result["message"].lower()


@pytest.mark.asyncio
async def test_add_task_xss_sanitization(test_user_id: str):
    """Test that XSS attempts are sanitized"""
    result = await add_task_handler(
        user_id=test_user_id,
        title="<script>alert('XSS')</script>",
        description="<img src=x onerror=alert('XSS')>"
    )

    # Task should be created but sanitized
    assert result["success"] is True
    # Check that dangerous HTML tags are escaped (not executed as HTML)
    assert "<script>" not in result["task"]["title"]
    assert "<img" not in result["task"]["description"]
    # Verify HTML entities are escaped
    assert "&lt;" in result["task"]["title"] or "script" not in result["task"]["title"].lower()
    assert "&lt;" in result["task"]["description"] or "img" not in result["task"]["description"].lower()


# ============================================================
# LIST_TASKS TESTS
# ============================================================

@pytest.mark.asyncio
async def test_list_tasks_empty(test_user_id: str):
    """Test listing tasks when user has no tasks"""
    result = await list_tasks_handler(user_id=test_user_id)

    assert result["success"] is True
    assert "tasks" in result
    assert len(result["tasks"]) == 0


@pytest.mark.asyncio
async def test_list_tasks_with_data(session: Session, test_user_id: str):
    """Test listing tasks when user has tasks"""
    # Create sample tasks
    task1 = Task(user_id=test_user_id, title="Task 1", completed=False)
    task2 = Task(user_id=test_user_id, title="Task 2", completed=True)
    session.add(task1)
    session.add(task2)
    session.commit()

    result = await list_tasks_handler(user_id=test_user_id)

    assert result["success"] is True
    assert len(result["tasks"]) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_completed(session: Session, test_user_id: str):
    """Test filtering tasks by completion status"""
    # Create mixed tasks
    task1 = Task(user_id=test_user_id, title="Incomplete", completed=False)
    task2 = Task(user_id=test_user_id, title="Complete", completed=True)
    task3 = Task(user_id=test_user_id, title="Also complete", completed=True)
    session.add_all([task1, task2, task3])
    session.commit()

    # List only completed tasks
    result = await list_tasks_handler(user_id=test_user_id, filter="completed")

    assert result["success"] is True
    assert len(result["tasks"]) == 2
    assert all(task["completed"] for task in result["tasks"])


@pytest.mark.asyncio
async def test_list_tasks_user_isolation(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that users only see their own tasks"""
    # Create tasks for different users
    task_user1 = Task(user_id=test_user_id, title="User 1 task", completed=False)
    task_user2 = Task(user_id=test_user_id_2, title="User 2 task", completed=False)
    session.add_all([task_user1, task_user2])
    session.commit()

    # List tasks for user 1
    result = await list_tasks_handler(user_id=test_user_id)

    assert result["success"] is True
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["title"] == "User 1 task"


# ============================================================
# COMPLETE_TASK TESTS
# ============================================================

@pytest.mark.asyncio
async def test_complete_task_success(session: Session, test_user_id: str):
    """Test successfully completing a task"""
    # Create an incomplete task
    task = Task(user_id=test_user_id, title="Finish report", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await complete_task_handler(
        user_id=test_user_id,
        task_id=task.id
    )

    assert result["success"] is True
    assert result["task"]["completed"] is True
    assert result["task"]["id"] == task.id


@pytest.mark.asyncio
async def test_complete_task_not_found(test_user_id: str):
    """Test completing a non-existent task"""
    result = await complete_task_handler(
        user_id=test_user_id,
        task_id=99999  # Non-existent ID
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
async def test_complete_task_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that users cannot complete other users' tasks"""
    # Create task for user 2
    task = Task(user_id=test_user_id_2, title="User 2 task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Try to complete with user 1's credentials
    result = await complete_task_handler(
        user_id=test_user_id,
        task_id=task.id
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"  # Should not reveal existence


@pytest.mark.asyncio
async def test_complete_already_completed_task(session: Session, test_user_id: str):
    """Test completing an already completed task (should be idempotent)"""
    # Create a completed task
    task = Task(user_id=test_user_id, title="Already done", completed=True)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await complete_task_handler(
        user_id=test_user_id,
        task_id=task.id
    )

    # Should succeed (idempotent operation)
    assert result["success"] is True
    assert result["task"]["completed"] is True


# ============================================================
# DELETE_TASK TESTS
# ============================================================

@pytest.mark.asyncio
async def test_delete_task_success(session: Session, test_user_id: str):
    """Test successfully deleting a task"""
    # Create a task
    task = Task(user_id=test_user_id, title="Delete me", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    result = await delete_task_handler(
        user_id=test_user_id,
        task_id=task_id
    )

    assert result["success"] is True
    assert result["deleted_task_id"] == task_id

    # Refresh session to see changes from handler's transaction
    session.expire_all()

    # Verify task is actually deleted
    deleted_task = session.get(Task, task_id)
    assert deleted_task is None


@pytest.mark.asyncio
async def test_delete_task_not_found(test_user_id: str):
    """Test deleting a non-existent task"""
    result = await delete_task_handler(
        user_id=test_user_id,
        task_id=99999
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"


@pytest.mark.asyncio
async def test_delete_task_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that users cannot delete other users' tasks"""
    # Create task for user 2
    task = Task(user_id=test_user_id_2, title="User 2 task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Try to delete with user 1's credentials
    result = await delete_task_handler(
        user_id=test_user_id,
        task_id=task.id
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"

    # Verify task still exists
    existing_task = session.get(Task, task.id)
    assert existing_task is not None


# ============================================================
# UPDATE_TASK TESTS
# ============================================================

@pytest.mark.asyncio
async def test_update_task_title(session: Session, test_user_id: str):
    """Test updating task title"""
    # Create a task
    task = Task(user_id=test_user_id, title="Old title", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        title="New title"
    )

    assert result["success"] is True
    assert result["task"]["title"] == "New title"


@pytest.mark.asyncio
async def test_update_task_description(session: Session, test_user_id: str):
    """Test updating task description"""
    task = Task(user_id=test_user_id, title="Task", description="Old desc", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        description="New description"
    )

    assert result["success"] is True
    assert result["task"]["description"] == "New description"
    assert result["task"]["title"] == "Task"  # Title unchanged


@pytest.mark.asyncio
async def test_update_task_completion_status(session: Session, test_user_id: str):
    """Test toggling task completion status"""
    task = Task(user_id=test_user_id, title="Task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        completed=True
    )

    assert result["success"] is True
    assert result["task"]["completed"] is True


@pytest.mark.asyncio
async def test_update_task_multiple_fields(session: Session, test_user_id: str):
    """Test updating multiple fields at once"""
    task = Task(
        user_id=test_user_id,
        title="Old title",
        description="Old desc",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        title="New title",
        description="New desc",
        completed=True
    )

    assert result["success"] is True
    assert result["task"]["title"] == "New title"
    assert result["task"]["description"] == "New desc"
    assert result["task"]["completed"] is True


@pytest.mark.asyncio
async def test_update_task_not_found(test_user_id: str):
    """Test updating a non-existent task"""
    result = await update_task_handler(
        user_id=test_user_id,
        task_id=99999,
        title="New title"
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"


@pytest.mark.asyncio
async def test_update_task_wrong_user(session: Session, test_user_id: str, test_user_id_2: str):
    """Test that users cannot update other users' tasks"""
    task = Task(user_id=test_user_id_2, title="User 2 task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        title="Hacked title"
    )

    assert result["success"] is False
    assert result["error"] == "NotFoundError"


@pytest.mark.asyncio
async def test_update_task_no_fields(session: Session, test_user_id: str):
    """Test updating task with no fields (should fail or return unchanged)"""
    task = Task(user_id=test_user_id, title="Task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id
        # No fields provided
    )

    # Depending on implementation, might fail or return unchanged task
    # Update based on actual behavior
    if result["success"]:
        assert result["task"]["title"] == "Task"  # Unchanged
    else:
        assert result["error"] == "ValidationError"


@pytest.mark.asyncio
async def test_update_task_validation_errors(session: Session, test_user_id: str):
    """Test update validation (empty title, too long, etc.)"""
    task = Task(user_id=test_user_id, title="Task", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Try to update with empty title
    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        title="   "  # Whitespace only
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"

    # Try to update with title too long
    result = await update_task_handler(
        user_id=test_user_id,
        task_id=task.id,
        title="A" * 201
    )

    assert result["success"] is False
    assert result["error"] == "ValidationError"
