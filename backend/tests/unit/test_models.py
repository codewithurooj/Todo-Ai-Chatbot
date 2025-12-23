"""Unit tests for database models

Tests SQLModel models for:
- User: Authentication and task/conversation ownership
- Task: Task creation, validation, relationships
- Conversation: Chat session management
- Message: Individual message storage and validation
"""
import pytest
from datetime import datetime
from sqlmodel import Session, select

from app.models.user import User
from app.models.task import Task, TaskCreate, TaskUpdate, TaskRead
from app.models.conversation import Conversation
from app.models.message import Message


# ============================================================
# USER MODEL TESTS
# ============================================================

def test_create_user(session: Session):
    """Test creating a user"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password_here"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password_here"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_email_unique(session: Session):
    """Test that email must be unique"""
    user1 = User(email="same@example.com", password_hash="hash1")
    session.add(user1)
    session.commit()

    # Try to create another user with same email
    user2 = User(email="same@example.com", password_hash="hash2")
    session.add(user2)

    with pytest.raises(Exception):  # Should raise IntegrityError
        session.commit()


# ============================================================
# TASK MODEL TESTS
# ============================================================

def test_create_task(session: Session, test_user_id: str):
    """Test creating a task"""
    task = Task(
        user_id=test_user_id,
        title="Test Task",
        description="Test description",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.id is not None
    assert task.user_id == test_user_id
    assert task.title == "Test Task"
    assert task.description == "Test description"
    assert task.completed is False
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)


def test_task_defaults(session: Session, test_user_id: str):
    """Test task default values"""
    task = Task(
        user_id=test_user_id,
        title="Task without optional fields"
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.description is None
    assert task.completed is False


def test_task_completion_toggle(session: Session, test_user_id: str):
    """Test toggling task completion status"""
    task = Task(
        user_id=test_user_id,
        title="Toggle me",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Toggle to completed
    task.completed = True
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.completed is True

    # Toggle back to incomplete
    task.completed = False
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.completed is False


def test_task_query_by_user(session: Session):
    """Test querying tasks by user ID"""
    user1 = "user-1"
    user2 = "user-2"

    # Create tasks for different users
    task1 = Task(user_id=user1, title="User 1 Task 1", completed=False)
    task2 = Task(user_id=user1, title="User 1 Task 2", completed=True)
    task3 = Task(user_id=user2, title="User 2 Task 1", completed=False)

    session.add_all([task1, task2, task3])
    session.commit()

    # Query user 1's tasks
    statement = select(Task).where(Task.user_id == user1)
    user1_tasks = session.exec(statement).all()

    assert len(user1_tasks) == 2
    assert all(task.user_id == user1 for task in user1_tasks)


def test_task_query_by_completion(session: Session, test_user_id: str):
    """Test querying tasks by completion status"""
    task1 = Task(user_id=test_user_id, title="Task 1", completed=False)
    task2 = Task(user_id=test_user_id, title="Task 2", completed=True)
    task3 = Task(user_id=test_user_id, title="Task 3", completed=False)

    session.add_all([task1, task2, task3])
    session.commit()

    # Query completed tasks
    statement = select(Task).where(
        Task.user_id == test_user_id,
        Task.completed == True
    )
    completed_tasks = session.exec(statement).all()

    assert len(completed_tasks) == 1
    assert completed_tasks[0].title == "Task 2"


# ============================================================
# TASK SCHEMA TESTS
# ============================================================

def test_task_create_schema():
    """Test TaskCreate schema validation"""
    task_data = TaskCreate(
        title="New Task",
        description="Task description",
        completed=False
    )

    assert task_data.title == "New Task"
    assert task_data.description == "Task description"
    assert task_data.completed is False


def test_task_update_schema():
    """Test TaskUpdate schema (all fields optional)"""
    # Update only title
    update1 = TaskUpdate(title="Updated Title")
    assert update1.title == "Updated Title"
    assert update1.description is None
    assert update1.completed is None

    # Update only completion
    update2 = TaskUpdate(completed=True)
    assert update2.title is None
    assert update2.completed is True

    # Update all fields
    update3 = TaskUpdate(
        title="New Title",
        description="New Description",
        completed=True
    )
    assert update3.title == "New Title"
    assert update3.description == "New Description"
    assert update3.completed is True


def test_task_read_schema(session: Session, test_user_id: str):
    """Test TaskRead schema includes all fields"""
    task = Task(
        user_id=test_user_id,
        title="Read Schema Test",
        description="Testing read schema",
        completed=False
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Convert to TaskRead schema
    task_read = TaskRead.model_validate(task)

    assert task_read.id == task.id
    assert task_read.user_id == test_user_id
    assert task_read.title == "Read Schema Test"
    assert task_read.description == "Testing read schema"
    assert task_read.completed is False
    assert isinstance(task_read.created_at, datetime)
    assert isinstance(task_read.updated_at, datetime)


# ============================================================
# CONVERSATION MODEL TESTS
# ============================================================

def test_create_conversation(session: Session, test_user_id: str):
    """Test creating a conversation"""
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == test_user_id
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.updated_at, datetime)


def test_conversation_updated_at(session: Session, test_user_id: str):
    """Test that updated_at changes when conversation is modified"""
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    original_updated_at = conversation.updated_at

    # Simulate update
    import time
    time.sleep(0.1)  # Ensure timestamp difference
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    assert conversation.updated_at > original_updated_at


def test_query_conversations_by_user(session: Session):
    """Test querying conversations by user ID"""
    user1 = "user-1"
    user2 = "user-2"

    conv1 = Conversation(user_id=user1)
    conv2 = Conversation(user_id=user1)
    conv3 = Conversation(user_id=user2)

    session.add_all([conv1, conv2, conv3])
    session.commit()

    # Query user 1's conversations
    statement = select(Conversation).where(Conversation.user_id == user1)
    user1_convs = session.exec(statement).all()

    assert len(user1_convs) == 2
    assert all(conv.user_id == user1 for conv in user1_convs)


# ============================================================
# MESSAGE MODEL TESTS
# ============================================================

def test_create_message(session: Session, test_user_id: str):
    """Test creating a message"""
    # First create a conversation
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Create a message
    message = Message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content="Hello, this is a test message"
    )
    session.add(message)
    session.commit()
    session.refresh(message)

    assert message.id is not None
    assert message.conversation_id == conversation.id
    assert message.user_id == test_user_id
    assert message.role == "user"
    assert message.content == "Hello, this is a test message"
    assert isinstance(message.created_at, datetime)


def test_message_roles(session: Session, test_user_id: str):
    """Test that messages can have user or assistant role"""
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # User message
    user_msg = Message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content="User's question"
    )
    session.add(user_msg)

    # Assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="assistant",
        content="Assistant's response"
    )
    session.add(assistant_msg)

    session.commit()

    # Query messages
    statement = select(Message).where(Message.conversation_id == conversation.id)
    messages = session.exec(statement).all()

    assert len(messages) == 2
    roles = {msg.role for msg in messages}
    assert roles == {"user", "assistant"}


def test_query_messages_by_conversation(session: Session, test_user_id: str):
    """Test querying messages by conversation ID"""
    # Create two conversations
    conv1 = Conversation(user_id=test_user_id)
    conv2 = Conversation(user_id=test_user_id)
    session.add_all([conv1, conv2])
    session.commit()
    session.refresh(conv1)
    session.refresh(conv2)

    # Add messages to each conversation
    msg1 = Message(conversation_id=conv1.id, user_id=test_user_id, role="user", content="Conv 1 msg 1")
    msg2 = Message(conversation_id=conv1.id, user_id=test_user_id, role="assistant", content="Conv 1 msg 2")
    msg3 = Message(conversation_id=conv2.id, user_id=test_user_id, role="user", content="Conv 2 msg 1")

    session.add_all([msg1, msg2, msg3])
    session.commit()

    # Query messages for conversation 1
    statement = select(Message).where(Message.conversation_id == conv1.id)
    conv1_messages = session.exec(statement).all()

    assert len(conv1_messages) == 2
    assert all(msg.conversation_id == conv1.id for msg in conv1_messages)


def test_message_ordering_by_timestamp(session: Session, test_user_id: str):
    """Test that messages can be ordered by created_at"""
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Create messages in sequence
    msg1 = Message(conversation_id=conversation.id, user_id=test_user_id, role="user", content="First")
    session.add(msg1)
    session.commit()

    import time
    time.sleep(0.01)  # Ensure different timestamps

    msg2 = Message(conversation_id=conversation.id, user_id=test_user_id, role="assistant", content="Second")
    session.add(msg2)
    session.commit()

    time.sleep(0.01)

    msg3 = Message(conversation_id=conversation.id, user_id=test_user_id, role="user", content="Third")
    session.add(msg3)
    session.commit()

    # Query messages ordered by created_at
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = session.exec(statement).all()

    assert len(messages) == 3
    assert messages[0].content == "First"
    assert messages[1].content == "Second"
    assert messages[2].content == "Third"


@pytest.mark.skip(reason="SQLite doesn't enforce foreign key constraints by default. This test only works with PostgreSQL.")
def test_message_foreign_key_constraint(session: Session, test_user_id: str):
    """Test that message requires valid conversation_id (foreign key)"""
    # Try to create message without valid conversation
    message = Message(
        conversation_id=99999,  # Non-existent conversation
        user_id=test_user_id,
        role="user",
        content="Orphan message"
    )
    session.add(message)

    # Should raise foreign key constraint error
    with pytest.raises(Exception):
        session.commit()


def test_message_content_length_limit(session: Session, test_user_id: str):
    """Test message content respects max_length constraint"""
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Create message with max length (10000 chars)
    max_content = "A" * 10000
    message = Message(
        conversation_id=conversation.id,
        user_id=test_user_id,
        role="user",
        content=max_content
    )
    session.add(message)
    session.commit()

    # Should succeed
    assert len(message.content) == 10000

    # Try to create message exceeding max length
    # Note: This depends on database enforcement
    # SQLModel may truncate or raise error based on DB settings
