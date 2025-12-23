# Data Model Specification

## Overview

Database schema for Todo AI Chatbot using SQLModel (Pydantic + SQLAlchemy). All tables include user isolation, timestamps, and proper constraints per Phase 3 constitution.

**Database**: Neon Serverless PostgreSQL
**ORM**: SQLModel
**Connection**: DATABASE_URL environment variable

---

## Entity Relationship Diagram (Textual)

```
┌──────────────┐
│    User      │
└──────┬───────┘
       │
       │ 1:N
       │
       ├─────────────┬──────────────┐
       │             │              │
       ▼             ▼              ▼
┌──────────┐  ┌──────────────┐  ┌────────────┐
│   Task   │  │ Conversation │  │            │
└──────────┘  └───────┬──────┘  │            │
                      │          │            │
                      │ 1:N      │            │
                      │          │            │
                      ▼          │            │
              ┌───────────┐      │            │
              │  Message  │◄─────┘            │
              └───────────┘                   │
```

**Relationships**:
- User has many Tasks (1:N)
- User has many Conversations (1:N)
- Conversation has many Messages (1:N)
- Message belongs to Conversation (N:1)

---

## Table: users

**Purpose**: Store authenticated user accounts

**Schema**:
```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class User(SQLModel, table=True):
    """User account for authentication and task/conversation ownership"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)  # Hashed via Better Auth
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (not columns, for SQLModel convenience)
    # tasks: List["Task"] = Relationship(back_populates="user")
    # conversations: List["Conversation"] = Relationship(back_populates="user")
```

**Indexes**:
- PRIMARY KEY (id)
- UNIQUE INDEX (email)

**Constraints**:
- email must be unique
- password_hash stored securely (never plain text)

**Notes**:
- Better Auth handles user creation and authentication
- password_hash managed by Better Auth, not directly by application

---

## Table: tasks

**Purpose**: Store user's todo tasks

**Schema**:
```python
class Task(SQLModel, table=True):
    """Todo task belonging to a user"""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    # user: User = Relationship(back_populates="tasks")
```

**Indexes**:
- PRIMARY KEY (id)
- INDEX (user_id) - for filtering tasks by user
- INDEX (user_id, completed) - for filtering pending/completed tasks

**Constraints**:
- user_id FOREIGN KEY references users(id) ON DELETE CASCADE
- title NOT NULL, length 1-200 chars
- description nullable, max 1000 chars
- completed default false

**Validation Rules**:
- Title cannot be empty or whitespace-only
- Title and description sanitized (no null bytes, HTML escaped)

---

## Table: conversations

**Purpose**: Store chat conversation sessions

**Schema**:
```python
class Conversation(SQLModel, table=True):
    """Chat conversation between user and AI assistant"""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    # user: User = Relationship(back_populates="conversations")
    # messages: List["Message"] = Relationship(back_populates="conversation")
```

**Indexes**:
- PRIMARY KEY (id)
- INDEX (user_id) - for listing user's conversations
- INDEX (user_id, updated_at DESC) - for sorting conversations by recent activity

**Constraints**:
- user_id FOREIGN KEY references users(id) ON DELETE CASCADE

**Notes**:
- updated_at is updated whenever a new message is added
- Conversations have no title or metadata (just container for messages)

---

## Table: messages

**Purpose**: Store individual messages within conversations

**Schema**:
```python
class Message(SQLModel, table=True):
    """Individual message in a conversation (user or assistant)"""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str = Field(max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    # conversation: Conversation = Relationship(back_populates="messages")
```

**Indexes**:
- PRIMARY KEY (id)
- INDEX (conversation_id, created_at ASC) - for retrieving messages chronologically
- INDEX (user_id) - for user isolation checks

**Constraints**:
- conversation_id FOREIGN KEY references conversations(id) ON DELETE CASCADE
- user_id FOREIGN KEY references users(id) ON DELETE CASCADE
- role must be "user" or "assistant" (check constraint)
- content NOT NULL, max 10000 chars

**Validation Rules**:
- role must be exactly "user" or "assistant"
- content length 1-10000 characters
- content sanitized (HTML escaped)

**Notes**:
- user_id denormalized for security (ensures message belongs to user who owns conversation)
- created_at defines message order (chronological)

---

## Database Migrations

**Tool**: Alembic (integrated with SQLModel)

**Migration Strategy**:
1. Initial migration creates all tables
2. Version control all migration scripts in `backend/migrations/`
3. Run migrations on deployment: `alembic upgrade head`

**Example Migration** (Initial Schema):
```python
"""Initial schema

Revision ID: 001_initial
Create Date: 2025-12-19
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('ix_tasks_user_completed', 'tasks', ['user_id', 'completed'])

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_user_updated', 'conversations', ['user_id', 'updated_at'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.String(10000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_role')
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('ix_messages_user_id', 'messages', ['user_id'])

def downgrade():
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('tasks')
    op.drop_table('users')
```

---

## Security Considerations

### User Isolation Enforcement

**CRITICAL**: All queries MUST filter by user_id

**Bad** (Vulnerable):
```sql
SELECT * FROM tasks WHERE id = ?;  -- ❌ Missing user_id filter
```

**Good** (Secure):
```sql
SELECT * FROM tasks WHERE id = ? AND user_id = ?;  -- ✅ User isolation enforced
```

### Cascade Deletes

When user is deleted:
- All tasks CASCADE DELETE (user's tasks removed)
- All conversations CASCADE DELETE
- All messages CASCADE DELETE (via conversation)

### Parameterized Queries

**Always use parameterized queries** (SQLModel handles this automatically):
```python
# SQLModel automatically parameterizes
task = session.exec(
    select(Task).where(Task.id == task_id, Task.user_id == user_id)
).first()
```

---

## Performance Optimization

### Connection Pooling

```python
# backend/database.py
from sqlmodel import create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Max 10 concurrent connections
    max_overflow=5,  # Allow 5 additional connections if pool full
    pool_timeout=30,  # Wait 30s for available connection
    pool_recycle=3600  # Recycle connections every hour
)
```

### Query Optimization

**Indexes** are critical for performance:
- tasks(user_id, completed) - for list_tasks filtering
- conversations(user_id, updated_at DESC) - for recent conversations
- messages(conversation_id, created_at ASC) - for chronological message retrieval

**Avoid N+1 Queries**:
```python
# Bad - N+1 query
for conversation in conversations:
    messages = session.exec(select(Message).where(Message.conversation_id == conversation.id)).all()

# Good - Single query with JOIN or eager loading
conversations_with_messages = session.exec(
    select(Conversation, Message)
    .join(Message)
    .where(Conversation.user_id == user_id)
).all()
```

---

## Testing Strategy

### Unit Tests

Test each model's:
- Field validation (length constraints, required fields)
- Default values (completed=false, timestamps)
- Constraints (unique email, foreign keys)

**Example**:
```python
def test_task_creation():
    task = Task(user_id=1, title="Buy groceries")
    assert task.completed == False
    assert task.created_at is not None

def test_task_title_validation():
    with pytest.raises(ValidationError):
        Task(user_id=1, title="")  # Empty title should fail
```

### Integration Tests

Test database operations:
- CRUD operations for each model
- Foreign key constraints (cascade deletes)
- User isolation (queries filtered by user_id)

**Example**:
```python
async def test_user_isolation():
    # User 1 creates task
    task = Task(user_id=1, title="User 1 task")
    session.add(task)
    session.commit()

    # User 2 cannot see User 1's task
    result = session.exec(
        select(Task).where(Task.id == task.id, Task.user_id == 2)
    ).first()
    assert result is None
```

---

## Database Schema Summary

**Tables**: 4 (users, tasks, conversations, messages)
**Foreign Keys**: 4 (all with CASCADE DELETE)
**Indexes**: 9 (optimized for common queries)
**Constraints**: Check constraint on message.role

**Estimated Row Counts** (per user):
- tasks: 0-1000 (average: 50)
- conversations: 1-100 (average: 10)
- messages: 20-2000 (average: 200)

**Storage Estimates**:
- 1000 users: ~50MB database size
- 10,000 users: ~500MB database size

---

**This data model enforces user isolation, supports stateless architecture, and provides efficient querying for the Todo AI Chatbot.**
