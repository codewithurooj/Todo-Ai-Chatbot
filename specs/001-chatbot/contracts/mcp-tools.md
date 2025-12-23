# MCP Tool Specifications

## Overview

This document defines the MCP (Model Context Protocol) tool interfaces for the Todo Chatbot. These tools provide task management operations that the OpenAI agent invokes based on user intent. All tools enforce user isolation and follow single-responsibility principles.

## Tool Catalog

| Tool Name | Purpose | Modifies Data | Auth Required | Idempotent |
|-----------|---------|---------------|---------------|------------|
| add_task | Create new task for user | Yes | Yes | No |
| list_tasks | Retrieve user's tasks with filtering | No | Yes | Yes |
| complete_task | Mark task as completed | Yes | Yes | Yes |
| update_task | Modify task title and/or description | Yes | Yes | No |
| delete_task | Permanently remove task | Yes | Yes | Yes |

---

## Tool: add_task

**Purpose:** Create a new task for the authenticated user

**Parameters:**
- `user_id` (integer, required) - User identifier (from JWT token, enforces ownership)
- `title` (string, required, 1-200 chars) - Task title displayed in task list
- `description` (string, optional, max 1000 chars) - Optional detailed task description

**Returns:**
- `success` (boolean) - Whether operation succeeded
- `task` (object) - Created task object
  - `id` (integer) - Unique task identifier
  - `user_id` (integer) - Owner user ID
  - `title` (string) - Task title
  - `description` (string | null) - Task description
  - `completed` (boolean) - Completion status (always false for new tasks)
  - `created_at` (ISO 8601 datetime) - Creation timestamp
  - `updated_at` (ISO 8601 datetime) - Last update timestamp

**Validation Rules:**
- Title must not be empty or whitespace-only
- Title length: 1-200 characters (UI truncates at 50 chars)
- Description length: max 1000 characters
- Description is optional (null if not provided)
- user_id must exist in users table (foreign key constraint)
- Title and description must not contain null bytes (\x00)

**Error Cases:**
- **ValidationError**: When title is empty, too long, or contains only whitespace
- **ValidationError**: When description exceeds 1000 characters
- **ValidationError**: When title or description contains null bytes
- **AuthorizationError**: When user_id doesn't match authenticated user (should never happen if orchestrator is correct)
- **DatabaseError**: When database is unavailable (safe to retry)

**Example:**
```json
// Input
{
  "user_id": 123,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread from Whole Foods"
}

// Output (Success)
{
  "success": true,
  "task": {
    "id": 456,
    "user_id": 123,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread from Whole Foods",
    "completed": false,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T10:30:00Z"
  }
}

// Output (Error - Title Too Long)
{
  "success": false,
  "error": "ValidationError",
  "message": "Title must be between 1 and 200 characters"
}
```

**Security Notes:**
- Verify user_id from request matches authenticated user
- Sanitize title and description to prevent XSS (escape HTML)
- Use parameterized SQL queries to prevent injection
- Rate limit: Max 100 tasks created per user per hour

**Idempotency:** No - calling twice with same title creates duplicate tasks. This is intentional (users may have multiple "Buy groceries" tasks for different days).

**Database Query:**
```sql
INSERT INTO tasks (user_id, title, description, completed, created_at, updated_at)
VALUES (?, ?, ?, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
RETURNING id, user_id, title, description, completed, created_at, updated_at;
```

---

## Tool: list_tasks

**Purpose:** Retrieve user's tasks with optional filtering by completion status

**Parameters:**
- `user_id` (integer, required) - User identifier (enforces ownership)
- `filter` (string, optional, default="pending") - Task filter
  - `"all"` - Return all tasks (completed and pending)
  - `"pending"` - Return only incomplete tasks
  - `"completed"` - Return only completed tasks
- `limit` (integer, optional, default=50, max=200) - Maximum number of tasks to return
- `offset` (integer, optional, default=0) - Pagination offset

**Returns:**
- `success` (boolean) - Whether operation succeeded
- `tasks` (array) - List of task objects
  - `id` (integer) - Task identifier
  - `user_id` (integer) - Owner user ID
  - `title` (string) - Task title
  - `description` (string | null) - Task description
  - `completed` (boolean) - Completion status
  - `created_at` (ISO 8601 datetime) - Creation timestamp
  - `updated_at` (ISO 8601 datetime) - Last update timestamp
- `total` (integer) - Total number of tasks matching filter (for pagination)
- `has_more` (boolean) - Whether more tasks exist beyond current page

**Validation Rules:**
- filter must be one of: "all", "pending", "completed"
- limit must be between 1 and 200
- offset must be non-negative

**Error Cases:**
- **ValidationError**: When filter is not one of allowed values
- **ValidationError**: When limit or offset are invalid
- **DatabaseError**: When database query fails (safe to retry)

**Example:**
```json
// Input
{
  "user_id": 123,
  "filter": "pending",
  "limit": 10,
  "offset": 0
}

// Output (Success)
{
  "success": true,
  "tasks": [
    {
      "id": 456,
      "user_id": 123,
      "title": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "created_at": "2025-12-19T10:30:00Z",
      "updated_at": "2025-12-19T10:30:00Z"
    },
    {
      "id": 457,
      "user_id": 123,
      "title": "Call dentist",
      "description": null,
      "completed": false,
      "created_at": "2025-12-19T11:00:00Z",
      "updated_at": "2025-12-19T11:00:00Z"
    }
  ],
  "total": 2,
  "has_more": false
}

// Output (Empty List)
{
  "success": true,
  "tasks": [],
  "total": 0,
  "has_more": false
}
```

**Security Notes:**
- Always filter by user_id to enforce user isolation
- Never return tasks belonging to other users
- Limit maximum page size to prevent resource exhaustion

**Idempotency:** Yes - safe to call multiple times with same parameters

**Database Query:**
```sql
-- For filter="pending"
SELECT id, user_id, title, description, completed, created_at, updated_at
FROM tasks
WHERE user_id = ? AND completed = false
ORDER BY created_at DESC
LIMIT ? OFFSET ?;

-- Count query for total
SELECT COUNT(*) FROM tasks WHERE user_id = ? AND completed = false;
```

---

## Tool: complete_task

**Purpose:** Mark an existing task as completed

**Parameters:**
- `user_id` (integer, required) - User identifier (enforces ownership)
- `task_id` (integer, required) - ID of task to complete

**Returns:**
- `success` (boolean) - Whether operation succeeded
- `task` (object) - Updated task object
  - `id` (integer) - Task identifier
  - `user_id` (integer) - Owner user ID
  - `title` (string) - Task title
  - `description` (string | null) - Task description
  - `completed` (boolean) - Completion status (always true after completion)
  - `created_at` (ISO 8601 datetime) - Creation timestamp
  - `updated_at` (ISO 8601 datetime) - Last update timestamp (updated to current time)

**Validation Rules:**
- task_id must be a positive integer
- Task must exist and belong to user_id

**Error Cases:**
- **ValidationError**: When task_id is not a positive integer
- **NotFoundError**: When task doesn't exist or doesn't belong to user
- **DatabaseError**: When database update fails (safe to retry)

**Example:**
```json
// Input
{
  "user_id": 123,
  "task_id": 456
}

// Output (Success)
{
  "success": true,
  "task": {
    "id": 456,
    "user_id": 123,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": true,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T15:45:00Z"
  }
}

// Output (Error - Not Found)
{
  "success": false,
  "error": "NotFoundError",
  "message": "Task not found or does not belong to user"
}
```

**Security Notes:**
- Always verify task belongs to user_id before updating
- Use WHERE clause with both task_id AND user_id

**Idempotency:** Yes - completing an already-completed task succeeds and returns the task (no error)

**Database Query:**
```sql
UPDATE tasks
SET completed = true, updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND user_id = ?
RETURNING id, user_id, title, description, completed, created_at, updated_at;

-- If no rows updated, task doesn't exist or doesn't belong to user
```

---

## Tool: update_task

**Purpose:** Modify an existing task's title and/or description

**Parameters:**
- `user_id` (integer, required) - User identifier (enforces ownership)
- `task_id` (integer, required) - ID of task to update
- `title` (string, optional, 1-200 chars) - New task title (if updating title)
- `description` (string, optional, max 1000 chars) - New task description (if updating description)

**Returns:**
- `success` (boolean) - Whether operation succeeded
- `task` (object) - Updated task object
  - `id` (integer) - Task identifier
  - `user_id` (integer) - Owner user ID
  - `title` (string) - Task title (new if provided, old if not)
  - `description` (string | null) - Task description (new if provided, old if not)
  - `completed` (boolean) - Completion status (unchanged)
  - `created_at` (ISO 8601 datetime) - Creation timestamp (unchanged)
  - `updated_at` (ISO 8601 datetime) - Last update timestamp (set to current time)

**Validation Rules:**
- At least one of title or description must be provided
- If title provided: 1-200 characters, not empty or whitespace-only
- If description provided: max 1000 characters
- Task must exist and belong to user_id
- Cannot change completed status (use complete_task for that)
- Cannot change user_id (security constraint)

**Error Cases:**
- **ValidationError**: When neither title nor description provided
- **ValidationError**: When title is empty, too long, or whitespace-only
- **ValidationError**: When description exceeds 1000 characters
- **NotFoundError**: When task doesn't exist or doesn't belong to user
- **DatabaseError**: When database update fails (safe to retry)

**Example:**
```json
// Input (Update Title Only)
{
  "user_id": 123,
  "task_id": 456,
  "title": "Buy groceries and milk"
}

// Output (Success)
{
  "success": true,
  "task": {
    "id": 456,
    "user_id": 123,
    "title": "Buy groceries and milk",
    "description": "Milk, eggs, bread",  // unchanged
    "completed": false,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T16:00:00Z"  // updated
  }
}

// Input (Update Both Title and Description)
{
  "user_id": 123,
  "task_id": 456,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread, and cheese"
}

// Output (Success)
{
  "success": true,
  "task": {
    "id": 456,
    "user_id": 123,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread, and cheese",
    "completed": false,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T16:05:00Z"
  }
}
```

**Security Notes:**
- Always verify task belongs to user_id before updating
- Never allow updating user_id (would enable unauthorized access)
- Never allow updating completed status via this tool (use complete_task)

**Idempotency:** No - updating with same values still updates updated_at timestamp. However, setting same title twice is functionally equivalent.

**Database Query:**
```sql
-- Dynamic query based on which fields are provided
UPDATE tasks
SET
    title = COALESCE(?, title),  -- Update if provided, keep old if null
    description = COALESCE(?, description),
    updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND user_id = ?
RETURNING id, user_id, title, description, completed, created_at, updated_at;
```

---

## Tool: delete_task

**Purpose:** Permanently remove a task from the user's task list

**Parameters:**
- `user_id` (integer, required) - User identifier (enforces ownership)
- `task_id` (integer, required) - ID of task to delete

**Returns:**
- `success` (boolean) - Whether operation succeeded
- `deleted_task_id` (integer) - ID of the deleted task
- `message` (string) - Confirmation message

**Validation Rules:**
- task_id must be a positive integer
- Task must exist and belong to user_id

**Error Cases:**
- **ValidationError**: When task_id is not a positive integer
- **NotFoundError**: When task doesn't exist or doesn't belong to user
- **DatabaseError**: When database deletion fails (safe to retry)

**Example:**
```json
// Input
{
  "user_id": 123,
  "task_id": 456
}

// Output (Success)
{
  "success": true,
  "deleted_task_id": 456,
  "message": "Task deleted successfully"
}

// Output (Error - Not Found)
{
  "success": false,
  "error": "NotFoundError",
  "message": "Task not found or does not belong to user"
}
```

**Security Notes:**
- Always verify task belongs to user_id before deleting
- Hard delete (permanent removal from database)
- Consider soft delete for audit trail (add deleted_at column) - currently not implemented

**Idempotency:** Yes - deleting an already-deleted task returns 404 NotFoundError (safe to retry once)

**Database Query:**
```sql
DELETE FROM tasks
WHERE id = ? AND user_id = ?
RETURNING id;

-- If no rows deleted, task doesn't exist or doesn't belong to user
```

---

## MCP Server Configuration

### Server Initialization

```python
# Conceptual server setup
from mcp.server import MCPServer

server = MCPServer(
    name="todo-task-manager",
    version="1.0.0",
    description="Task management tools for Todo chatbot"
)

# Register all tools
server.register_tool(add_task)
server.register_tool(list_tasks)
server.register_tool(complete_task)
server.register_tool(update_task)
server.register_tool(delete_task)

# Start server
server.start(port=8001)
```

### Tool Registration Format

Each tool follows this registration pattern:

```python
@server.tool(
    name="add_task",
    description="Create a new task for the user",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "integer", "description": "User identifier"},
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "description": {"type": "string", "maxLength": 1000}
        },
        "required": ["user_id", "title"]
    }
)
async def add_task(user_id: int, title: str, description: str = None):
    # Implementation
    pass
```

---

## Common Validation Patterns

### Input Validation

**String Fields**:
```python
def validate_title(title: str) -> tuple[bool, str]:
    if not title or title.strip() == "":
        return False, "Title cannot be empty"
    if len(title) > 200:
        return False, "Title must be 200 characters or less"
    if '\x00' in title:
        return False, "Title contains invalid characters"
    return True, ""
```

**Integer Fields**:
```python
def validate_task_id(task_id: int) -> tuple[bool, str]:
    if not isinstance(task_id, int):
        return False, "task_id must be an integer"
    if task_id < 1:
        return False, "task_id must be positive"
    return True, ""
```

**Enum Fields**:
```python
def validate_filter(filter_value: str) -> tuple[bool, str]:
    allowed = ["all", "pending", "completed"]
    if filter_value not in allowed:
        return False, f"filter must be one of: {', '.join(allowed)}"
    return True, ""
```

### User Authorization

**Every tool must validate ownership**:
```python
async def verify_task_ownership(task_id: int, user_id: int, db_session):
    task = await db_session.get(Task, task_id)
    if not task:
        raise NotFoundError("Task not found")
    if task.user_id != user_id:
        raise AuthorizationError("Task does not belong to user")
    return task
```

---

## Error Response Format

All tools return errors in consistent format:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message"
}
```

**Error Types**:
- `ValidationError` - Invalid input parameters
- `NotFoundError` - Resource doesn't exist
- `AuthorizationError` - User doesn't own the resource
- `DatabaseError` - Database operation failed

---

## Testing Recommendations

### Unit Tests

**Test each tool with**:
- Valid inputs (happy path)
- Invalid inputs (validation errors)
- Missing required parameters
- Edge cases (empty strings, max lengths, null values)
- User isolation (accessing other user's tasks)

**Example Test**:
```python
async def test_add_task_success():
    result = await add_task(
        user_id=123,
        title="Buy groceries",
        description="Milk and eggs"
    )
    assert result["success"] == True
    assert result["task"]["title"] == "Buy groceries"
    assert result["task"]["completed"] == False

async def test_add_task_empty_title():
    result = await add_task(user_id=123, title="")
    assert result["success"] == False
    assert result["error"] == "ValidationError"
```

### Integration Tests

**Test tool invocation via MCP protocol**:
- Tool registration
- Parameter marshalling
- Response unmarshalling
- Error handling

---

## Performance Considerations

- **Database Indexes**: Ensure indexes on `user_id` and `completed` for efficient filtering
- **Connection Pooling**: Use database connection pool for concurrent requests
- **Query Limits**: Always limit list_tasks queries (max 200 items)
- **Timeouts**: Set 10-second timeout for tool execution

---

## Security Checklist

- [x] All tools require user_id parameter
- [x] All database queries filter by user_id
- [x] Input validation prevents injection attacks
- [x] String inputs sanitized (null byte check, HTML escape)
- [x] Rate limiting prevents abuse
- [x] Error messages don't leak sensitive information
- [x] Database queries use parameterized statements

---

**These MCP tools provide the core task management functionality for the Todo Chatbot. They enforce user isolation, validate all inputs, and return structured responses that the OpenAI agent can use to generate natural language confirmations.**
