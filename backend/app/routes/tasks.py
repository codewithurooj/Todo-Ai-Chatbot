"""Task CRUD API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models.task import Task, TaskCreate, TaskUpdate, TaskRead
from app.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    List all tasks for the authenticated user.

    Args:
        user_id: User ID from path parameter
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        List of tasks for the user

    Raises:
        HTTPException: If user_id doesn't match JWT token
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to user's tasks"
        )

    # Query tasks for user
    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()

    return tasks


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    user_id: str,
    task: TaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Create a new task for the authenticated user.

    Args:
        user_id: User ID from path parameter
        task: Task data to create
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Created task

    Raises:
        HTTPException: If user_id doesn't match JWT token
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Create task
    db_task = Task(**task.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Get a specific task by ID.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to retrieve
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Task details

    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not task or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    user_id: str,
    task_id: int,
    task_update: TaskUpdate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Update a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to update
        task_update: Updated task data
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task

    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    db_task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update task fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    # Update timestamp
    db_task.updated_at = datetime.utcnow()

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Delete a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to delete
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not task or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Delete task
    session.delete(task)
    session.commit()


@router.patch("/{task_id}/complete", response_model=TaskRead)
async def toggle_complete(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Toggle task completion status.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to toggle
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task

    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    db_task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Toggle completion
    db_task.completed = not db_task.completed
    db_task.updated_at = datetime.utcnow()

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task
