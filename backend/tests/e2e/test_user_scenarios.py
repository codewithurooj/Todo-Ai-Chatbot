"""End-to-end tests for user scenarios

Tests complete user workflows from start to finish:
- User creates task via chat
- User lists tasks
- User completes task
- User deletes task
- Multi-turn conversation with context
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlmodel import Session, select

from app.models.task import Task
from app.models.conversation import Conversation
from app.models.message import Message


# ============================================================
# SCENARIO: CREATE TASK VIA CHAT
# ============================================================

@pytest.mark.e2e
def test_user_creates_task_via_chat(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User creates a task through conversational interface

    Flow:
    1. User sends message: "I need to buy groceries"
    2. AI detects intent and calls add_task tool
    3. Task is created in database
    4. AI confirms task creation to user
    """
    # Configure the autouse mock for this specific test
    # First call: AI decides to use add_task tool
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "add_task"
    mock_tool_call.function.arguments = '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # Second call: AI confirms task creation
    mock_choice2 = Mock()
    mock_choice2.message.content = "I've added 'Buy groceries' to your task list!"
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    # User sends message
    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "I need to buy groceries - milk, eggs, and bread"},
        headers=auth_headers
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "Buy groceries" in data["response"] or "added" in data["response"].lower()

    # Verify task was created in database
    statement = select(Task).where(Task.user_id == test_user_id)
    tasks = session.exec(statement).all()

    assert len(tasks) == 1
    assert tasks[0].title == "Buy groceries"
    assert tasks[0].description == "Milk, eggs, bread"
    assert tasks[0].completed is False


# ============================================================
# SCENARIO: LIST TASKS VIA CHAT
# ============================================================

@pytest.mark.e2e
def test_user_lists_tasks_via_chat(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User asks to see their tasks

    Flow:
    1. Create some tasks in database
    2. User sends message: "What are my tasks?"
    3. AI calls list_tasks tool
    4. AI presents tasks to user in friendly format
    """
    # Setup: Create some tasks
    task1 = Task(user_id=test_user_id, title="Buy groceries", completed=False)
    task2 = Task(user_id=test_user_id, title="Call dentist", completed=False)
    task3 = Task(user_id=test_user_id, title="Finish report", completed=True)
    session.add_all([task1, task2, task3])
    session.commit()

    # Configure the autouse mock for this specific test
    # AI calls list_tasks
    mock_tool_call = Mock()
    mock_tool_call.id = "call_list"
    mock_tool_call.function.name = "list_tasks"
    mock_tool_call.function.arguments = '{}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # AI presents tasks
    mock_choice2 = Mock()
    mock_choice2.message.content = "You have 3 tasks: Buy groceries, Call dentist, and Finish report (completed)."
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "What are my tasks?"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify tool was called
    assert "tool_calls" in data
    assert data["tool_calls"][0]["tool"] == "list_tasks"
    assert data["tool_calls"][0]["result"]["success"] is True


# ============================================================
# SCENARIO: COMPLETE TASK VIA CHAT
# ============================================================

@pytest.mark.e2e
def test_user_completes_task_via_chat(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User marks a task as complete

    Flow:
    1. Create a task
    2. User sends message: "I finished buying groceries"
    3. AI calls complete_task tool
    4. Task is marked complete in database
    5. AI confirms completion
    """
    # Setup: Create a task
    task = Task(user_id=test_user_id, title="Buy groceries", completed=False)
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    # Configure the autouse mock for this specific test
    # AI calls complete_task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_complete"
    mock_tool_call.function.name = "complete_task"
    mock_tool_call.function.arguments = f'{{"task_id": {task_id}}}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # AI confirms
    mock_choice2 = Mock()
    mock_choice2.message.content = "Great! I've marked 'Buy groceries' as complete."
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "I finished buying groceries"},
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify task is marked complete in database
    session.refresh(task)
    assert task.completed is True


# ============================================================
# SCENARIO: DELETE TASK VIA CHAT
# ============================================================

@pytest.mark.e2e
def test_user_deletes_task_via_chat(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User removes a task

    Flow:
    1. Create a task
    2. User sends message: "Delete the grocery task"
    3. AI calls delete_task tool
    4. Task is removed from database
    5. AI confirms deletion
    """
    # Setup: Create a task
    task = Task(user_id=test_user_id, title="Buy groceries", completed=True)
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    # Configure the autouse mock for this specific test
    # AI calls delete_task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_delete"
    mock_tool_call.function.name = "delete_task"
    mock_tool_call.function.arguments = f'{{"task_id": {task_id}}}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # AI confirms
    mock_choice2 = Mock()
    mock_choice2.message.content = "I've removed 'Buy groceries' from your task list."
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Delete the grocery task"},
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify task is deleted from database
    deleted_task = session.get(Task, task_id)
    assert deleted_task is None


# ============================================================
# SCENARIO: MULTI-TURN CONVERSATION WITH CONTEXT
# ============================================================

@pytest.mark.e2e
def test_multi_turn_conversation_with_context(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User has multi-turn conversation with context maintained

    Flow:
    1. User: "Add a task to buy milk"
    2. AI: Creates task, confirms
    3. User: "Add another one for calling the dentist"
    4. AI: Uses context, creates second task
    5. User: "Show me both tasks"
    6. AI: Lists both tasks created in this conversation
    """
    conversation_id = None

    # Turn 1: Add first task
    mock_tool_call1 = Mock()
    mock_tool_call1.id = "call_1"
    mock_tool_call1.function.name = "add_task"
    mock_tool_call1.function.arguments = '{"title": "Buy milk"}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call1]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    mock_choice1b = Mock()
    mock_choice1b.message.content = "I've added 'Buy milk' to your tasks."
    mock_choice1b.message.tool_calls = None
    mock_choice1b.finish_reason = "stop"

    mock_response1b = Mock()
    mock_response1b.choices = [mock_choice1b]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response1b]

    response1 = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Add a task to buy milk"},
        headers=auth_headers
    )

    assert response1.status_code == 200
    conversation_id = response1.json()["conversation_id"]

    # Turn 2: Add second task (using context)
    mock_tool_call2 = Mock()
    mock_tool_call2.id = "call_2"
    mock_tool_call2.function.name = "add_task"
    mock_tool_call2.function.arguments = '{"title": "Call dentist"}'

    mock_choice2 = Mock()
    mock_choice2.message.content = ""
    mock_choice2.message.tool_calls = [mock_tool_call2]
    mock_choice2.finish_reason = "tool_calls"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_choice2b = Mock()
    mock_choice2b.message.content = "I've added 'Call dentist' to your tasks as well."
    mock_choice2b.message.tool_calls = None
    mock_choice2b.finish_reason = "stop"

    mock_response2b = Mock()
    mock_response2b.choices = [mock_choice2b]

    mock_openai_client.chat.completions.create.side_effect = [mock_response2, mock_response2b]

    response2 = client.post(
        f"/api/{test_user_id}/chat",
        json={
            "message": "Add another one for calling the dentist",
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )

    assert response2.status_code == 200

    # Turn 3: List tasks
    mock_tool_call3 = Mock()
    mock_tool_call3.id = "call_3"
    mock_tool_call3.function.name = "list_tasks"
    mock_tool_call3.function.arguments = '{}'

    mock_choice3 = Mock()
    mock_choice3.message.content = ""
    mock_choice3.message.tool_calls = [mock_tool_call3]
    mock_choice3.finish_reason = "tool_calls"

    mock_response3 = Mock()
    mock_response3.choices = [mock_choice3]

    mock_choice3b = Mock()
    mock_choice3b.message.content = "Here are your tasks: Buy milk and Call dentist."
    mock_choice3b.message.tool_calls = None
    mock_choice3b.finish_reason = "stop"

    mock_response3b = Mock()
    mock_response3b.choices = [mock_choice3b]

    mock_openai_client.chat.completions.create.side_effect = [mock_response3, mock_response3b]

    response3 = client.post(
        f"/api/{test_user_id}/chat",
        json={
            "message": "Show me both tasks",
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )

    assert response3.status_code == 200

    # Verify conversation has all messages
    statement = select(Message).where(Message.conversation_id == conversation_id)
    messages = session.exec(statement).all()

    # Should have at least 4 messages (Turn 1: user+assistant, Turn 2: user+assistant)
    # May have 6 if Turn 3 messages are persisted
    assert len(messages) >= 4
    user_messages = [m for m in messages if m.role == "user"]
    assert len(user_messages) >= 2

    # Verify tasks were created
    statement = select(Task).where(Task.user_id == test_user_id)
    tasks = session.exec(statement).all()

    assert len(tasks) == 2
    task_titles = {task.title for task in tasks}
    assert "Buy milk" in task_titles
    assert "Call dentist" in task_titles


# ============================================================
# SCENARIO: UPDATE TASK VIA CHAT
# ============================================================

@pytest.mark.e2e
def test_user_updates_task_via_chat(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: User modifies an existing task

    Flow:
    1. Create a task
    2. User: "Change the grocery task to include cheese"
    3. AI calls update_task tool
    4. Task is updated in database
    5. AI confirms update
    """
    # Setup: Create a task
    task = Task(
        user_id=test_user_id,
        title="Buy groceries",
        description="Milk and bread",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    # Configure the autouse mock for this specific test
    # AI calls update_task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_update"
    mock_tool_call.function.name = "update_task"
    mock_tool_call.function.arguments = f'{{"task_id": {task_id}, "description": "Milk, bread, and cheese"}}'

    mock_choice1 = Mock()
    mock_choice1.message.content = ""
    mock_choice1.message.tool_calls = [mock_tool_call]
    mock_choice1.finish_reason = "tool_calls"

    mock_response1 = Mock()
    mock_response1.choices = [mock_choice1]

    # AI confirms
    mock_choice2 = Mock()
    mock_choice2.message.content = "I've updated the grocery task to include cheese."
    mock_choice2.message.tool_calls = None
    mock_choice2.finish_reason = "stop"

    mock_response2 = Mock()
    mock_response2.choices = [mock_choice2]

    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Change the grocery task to include cheese"},
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify task was updated
    session.refresh(task)
    assert "cheese" in task.description.lower()


# ============================================================
# SCENARIO: FULL TASK LIFECYCLE
# ============================================================

@pytest.mark.e2e
def test_full_task_lifecycle(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict,
    session: Session,
    mock_openai_client: Mock
):
    """
    E2E Scenario: Complete task lifecycle from creation to deletion

    Flow:
    1. User creates task
    2. User lists tasks (sees new task)
    3. User completes task
    4. User lists tasks (sees task is completed)
    5. User deletes task
    6. User lists tasks (task is gone)
    """
    conversation_id = None

    # Step 1: Create task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_create"
    mock_tool_call.function.name = "add_task"
    mock_tool_call.function.arguments = '{"title": "Write report"}'

    mock_choice = Mock()
    mock_choice.message.content = ""
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.finish_reason = "tool_calls"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_choice_confirm = Mock()
    mock_choice_confirm.message.content = "Task created!"
    mock_choice_confirm.message.tool_calls = None
    mock_choice_confirm.finish_reason = "stop"

    mock_response_confirm = Mock()
    mock_response_confirm.choices = [mock_choice_confirm]

    mock_openai_client.chat.completions.create.side_effect = [mock_response, mock_response_confirm]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={"message": "Add task: write report"},
        headers=auth_headers
    )

    conversation_id = response.json()["conversation_id"]

    # Get the created task ID
    statement = select(Task).where(Task.user_id == test_user_id, Task.title == "Write report")
    task = session.exec(statement).first()
    assert task is not None
    task_id = task.id

    # Verify task exists and is incomplete
    assert task.completed is False

    # Step 2: Complete task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_complete"
    mock_tool_call.function.name = "complete_task"
    mock_tool_call.function.arguments = f'{{"task_id": {task_id}}}'

    mock_choice = Mock()
    mock_choice.message.content = ""
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.finish_reason = "tool_calls"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_choice_confirm = Mock()
    mock_choice_confirm.message.content = "Task completed!"
    mock_choice_confirm.message.tool_calls = None
    mock_choice_confirm.finish_reason = "stop"

    mock_response_confirm = Mock()
    mock_response_confirm.choices = [mock_choice_confirm]

    mock_openai_client.chat.completions.create.side_effect = [mock_response, mock_response_confirm]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={
            "message": "I finished the report",
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )

    # Verify task is completed
    session.refresh(task)
    assert task.completed is True

    # Step 3: Delete task
    mock_tool_call = Mock()
    mock_tool_call.id = "call_delete"
    mock_tool_call.function.name = "delete_task"
    mock_tool_call.function.arguments = f'{{"task_id": {task_id}}}'

    mock_choice = Mock()
    mock_choice.message.content = ""
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_choice.finish_reason = "tool_calls"

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_choice_confirm = Mock()
    mock_choice_confirm.message.content = "Task deleted!"
    mock_choice_confirm.message.tool_calls = None
    mock_choice_confirm.finish_reason = "stop"

    mock_response_confirm = Mock()
    mock_response_confirm.choices = [mock_choice_confirm]

    mock_openai_client.chat.completions.create.side_effect = [mock_response, mock_response_confirm]

    response = client.post(
        f"/api/{test_user_id}/chat",
        json={
            "message": "Delete the report task",
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )

    # Verify task is deleted
    deleted_task = session.get(Task, task_id)
    assert deleted_task is None
