# Feature Specification: MCP Tools for AI Todo Management

**Feature Branch**: `003-mcp-tools-spec`
**Created**: 2025-12-19
**Status**: Draft
**Input**: User description: "Create an MCP tools specification for AI agent todo management tools"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent Creates Tasks via MCP (Priority: P1)

The AI agent receives a user's natural language request to create a task and invokes the `add_task` MCP tool to persist the task to the database, ensuring the task is associated with the correct user.

**Why this priority**: Task creation is the foundational operation for any todo system. Without the ability to create tasks, no other operations are possible.

**Independent Test**: AI agent calls `add_task` with user_id, title, and optional description. Tool returns the created task with assigned ID and timestamps. Value delivered: Tasks are successfully persisted and retrievable.

**Acceptance Scenarios**:

1. **Given** an AI agent processing user request "add buy groceries", **When** it calls `add_task(user_id=123, title="Buy groceries")`, **Then** the tool returns a task object with id, user_id=123, title="Buy groceries", completed=false, and timestamp fields
2. **Given** an AI agent with a detailed task request, **When** it calls `add_task(user_id=456, title="Project report", description="Complete Q4 financial report")`, **Then** the tool creates a task with both title and description fields populated
3. **Given** an AI agent calls `add_task` without required user_id, **When** the tool validates inputs, **Then** it returns an error indicating user_id is required
4. **Given** an AI agent calls `add_task` with empty title, **When** the tool validates inputs, **Then** it returns an error indicating title cannot be empty

---

### User Story 2 - AI Agent Retrieves Task Lists via MCP (Priority: P1)

The AI agent needs to show a user their tasks and invokes the `list_tasks` MCP tool to retrieve all tasks for that specific user, with optional filtering by completion status.

**Why this priority**: Without the ability to retrieve tasks, users cannot see what they've created. This is essential for any task management workflow and enables the agent to provide context-aware responses.

**Independent Test**: AI agent calls `list_tasks` with user_id and receives an array of all tasks belonging to that user. Value delivered: Complete visibility of user's task list.

**Acceptance Scenarios**:

1. **Given** user 123 has 5 tasks (3 incomplete, 2 complete), **When** the AI agent calls `list_tasks(user_id=123)`, **Then** the tool returns all 5 tasks sorted by creation date
2. **Given** user 123 has tasks, **When** the AI agent calls `list_tasks(user_id=123, completed=false)`, **Then** the tool returns only incomplete tasks
3. **Given** user 123 has tasks, **When** the AI agent calls `list_tasks(user_id=123, completed=true)`, **Then** the tool returns only completed tasks
4. **Given** user 456 has no tasks, **When** the AI agent calls `list_tasks(user_id=456)`, **Then** the tool returns an empty array
5. **Given** the AI agent calls `list_tasks` without user_id, **When** the tool validates inputs, **Then** it returns an error indicating user_id is required
6. **Given** user 123 has tasks but AI agent requests user 456's tasks, **When** the tool executes, **Then** it returns only user 456's tasks (proper isolation)

---

### User Story 3 - AI Agent Marks Tasks Complete via MCP (Priority: P1)

The AI agent processes a user's completion statement and invokes the `complete_task` MCP tool to update the task's completion status, ensuring only the task owner can mark their tasks complete.

**Why this priority**: Task completion is the primary workflow outcome. Users need to track progress by marking tasks as done, making this a core operation.

**Independent Test**: AI agent calls `complete_task` with user_id and task_id. Tool updates the task's completed flag to true and returns the updated task. Value delivered: Progress tracking through completion status.

**Acceptance Scenarios**:

1. **Given** user 123 has an incomplete task with id=10, **When** the AI agent calls `complete_task(user_id=123, task_id=10)`, **Then** the tool updates the task to completed=true and returns the updated task
2. **Given** user 123 has a completed task with id=11, **When** the AI agent calls `complete_task(user_id=123, task_id=11)`, **Then** the tool successfully processes (idempotent - already complete)
3. **Given** user 123 tries to complete task id=99 which doesn't exist, **When** the AI agent calls `complete_task(user_id=123, task_id=99)`, **Then** the tool returns an error "Task not found"
4. **Given** user 123 tries to complete task id=20 owned by user 456, **When** the AI agent calls `complete_task(user_id=123, task_id=20)`, **Then** the tool returns an error "Task not found" (maintains user isolation)
5. **Given** the AI agent calls `complete_task` without required parameters, **When** the tool validates inputs, **Then** it returns an error indicating which parameters are missing

---

### User Story 4 - AI Agent Updates Task Details via MCP (Priority: P2)

The AI agent interprets a user's request to modify a task and invokes the `update_task` MCP tool to change the task's title or description, ensuring only the task owner can update their tasks.

**Why this priority**: While less critical than creating and completing tasks, updating allows users to correct mistakes or adapt tasks as requirements change without recreating them.

**Independent Test**: AI agent calls `update_task` with user_id, task_id, and fields to update. Tool modifies the specified fields and returns the updated task. Value delivered: Flexible task management without data loss.

**Acceptance Scenarios**:

1. **Given** user 123 has a task with id=10, title="Buy groceries", **When** the AI agent calls `update_task(user_id=123, task_id=10, title="Buy groceries and milk")`, **Then** the tool updates the title and returns the modified task
2. **Given** user 123 has a task with id=10, **When** the AI agent calls `update_task(user_id=123, task_id=10, description="Including bread and eggs")`, **Then** the tool updates only the description field
3. **Given** user 123 has a task with id=10, **When** the AI agent calls `update_task(user_id=123, task_id=10, title="New title", description="New description")`, **Then** the tool updates both fields simultaneously
4. **Given** user 123 tries to update task id=99 which doesn't exist, **When** the AI agent calls `update_task(user_id=123, task_id=99, title="Test")`, **Then** the tool returns an error "Task not found"
5. **Given** user 123 tries to update task id=20 owned by user 456, **When** the AI agent calls `update_task`, **Then** the tool returns an error "Task not found" (maintains user isolation)
6. **Given** the AI agent calls `update_task` with empty title, **When** the tool validates inputs, **Then** it returns an error indicating title cannot be empty

---

### User Story 5 - AI Agent Deletes Tasks via MCP (Priority: P2)

The AI agent processes a user's deletion request and invokes the `delete_task` MCP tool to permanently remove the task, ensuring only the task owner can delete their tasks.

**Why this priority**: While users can leave unwanted tasks incomplete rather than deleting them, deletion provides a cleaner interface and allows users to remove mistakes or obsolete tasks.

**Independent Test**: AI agent calls `delete_task` with user_id and task_id. Tool removes the task from storage and confirms deletion. Value delivered: Clean task list maintenance.

**Acceptance Scenarios**:

1. **Given** user 123 has a task with id=10, **When** the AI agent calls `delete_task(user_id=123, task_id=10)`, **Then** the tool deletes the task and returns a success confirmation
2. **Given** user 123 tries to delete task id=99 which doesn't exist, **When** the AI agent calls `delete_task(user_id=123, task_id=99)`, **Then** the tool returns an error "Task not found"
3. **Given** user 123 tries to delete task id=20 owned by user 456, **When** the AI agent calls `delete_task(user_id=123, task_id=20)`, **Then** the tool returns an error "Task not found" (maintains user isolation)
4. **Given** the AI agent calls `delete_task` without required parameters, **When** the tool validates inputs, **Then** it returns an error indicating which parameters are missing
5. **Given** user 123 deletes task id=10, **When** the AI agent immediately calls `list_tasks(user_id=123)`, **Then** the deleted task does not appear in the results

---

### Edge Cases

- What happens when a tool receives a user_id that doesn't exist in the system? (Should still work - user isolation is based on JWT, not user existence check)
- How do tools handle extremely long titles or descriptions (>10,000 characters)?
- What happens if the database connection fails during a tool call?
- How do tools handle concurrent updates to the same task by the same user?
- What happens when a tool receives malformed parameters (wrong types, negative IDs)?
- How do tools handle special characters, emojis, or non-English text in titles/descriptions?
- What happens if a user tries to create thousands of tasks rapidly?
- How are timestamps handled across different timezones?

## Requirements *(mandatory)*

### Functional Requirements

#### Tool: add_task

- **FR-001**: The `add_task` tool MUST accept a `user_id` parameter (required, integer)
- **FR-002**: The `add_task` tool MUST accept a `title` parameter (required, string, 1-500 characters)
- **FR-003**: The `add_task` tool MUST accept a `description` parameter (optional, string, 0-2000 characters)
- **FR-004**: The `add_task` tool MUST create a new task record associated with the provided user_id
- **FR-005**: The `add_task` tool MUST assign a unique task ID automatically
- **FR-006**: The `add_task` tool MUST set `completed` to false by default
- **FR-007**: The `add_task` tool MUST capture creation timestamp automatically
- **FR-008**: The `add_task` tool MUST return the complete task object including all assigned fields
- **FR-009**: The `add_task` tool MUST return an error if user_id is missing or invalid
- **FR-010**: The `add_task` tool MUST return an error if title is empty or exceeds length limits

#### Tool: list_tasks

- **FR-011**: The `list_tasks` tool MUST accept a `user_id` parameter (required, integer)
- **FR-012**: The `list_tasks` tool MUST accept a `completed` parameter (optional, boolean)
- **FR-013**: The `list_tasks` tool MUST return all tasks belonging to the specified user_id when no filter is applied
- **FR-014**: The `list_tasks` tool MUST filter results by completion status when `completed` parameter is provided
- **FR-015**: The `list_tasks` tool MUST return tasks sorted by creation date (newest first)
- **FR-016**: The `list_tasks` tool MUST return an empty array if the user has no tasks
- **FR-017**: The `list_tasks` tool MUST NOT return tasks belonging to other users under any circumstances
- **FR-018**: The `list_tasks` tool MUST return an error if user_id is missing or invalid

#### Tool: complete_task

- **FR-019**: The `complete_task` tool MUST accept a `user_id` parameter (required, integer)
- **FR-020**: The `complete_task` tool MUST accept a `task_id` parameter (required, integer)
- **FR-021**: The `complete_task` tool MUST set the task's `completed` field to true
- **FR-022**: The `complete_task` tool MUST update the task's `updated_at` timestamp
- **FR-023**: The `complete_task` tool MUST return the updated task object
- **FR-024**: The `complete_task` tool MUST be idempotent (calling multiple times has same effect as calling once)
- **FR-025**: The `complete_task` tool MUST return an error if the task doesn't exist or belongs to a different user
- **FR-026**: The `complete_task` tool MUST return an error if user_id or task_id is missing or invalid

#### Tool: update_task

- **FR-027**: The `update_task` tool MUST accept a `user_id` parameter (required, integer)
- **FR-028**: The `update_task` tool MUST accept a `task_id` parameter (required, integer)
- **FR-029**: The `update_task` tool MUST accept a `title` parameter (optional, string, 1-500 characters)
- **FR-030**: The `update_task` tool MUST accept a `description` parameter (optional, string, 0-2000 characters)
- **FR-031**: The `update_task` tool MUST update only the fields that are provided
- **FR-032**: The `update_task` tool MUST NOT modify the task's ID, user_id, completed status, or created_at timestamp
- **FR-033**: The `update_task` tool MUST update the task's `updated_at` timestamp
- **FR-034**: The `update_task` tool MUST return the updated task object
- **FR-035**: The `update_task` tool MUST return an error if the task doesn't exist or belongs to a different user
- **FR-036**: The `update_task` tool MUST return an error if user_id or task_id is missing or invalid
- **FR-037**: The `update_task` tool MUST return an error if title is provided but empty or exceeds length limits

#### Tool: delete_task

- **FR-038**: The `delete_task` tool MUST accept a `user_id` parameter (required, integer)
- **FR-039**: The `delete_task` tool MUST accept a `task_id` parameter (required, integer)
- **FR-040**: The `delete_task` tool MUST permanently remove the task from storage
- **FR-041**: The `delete_task` tool MUST return a success confirmation including the deleted task_id
- **FR-042**: The `delete_task` tool MUST return an error if the task doesn't exist or belongs to a different user
- **FR-043**: The `delete_task` tool MUST return an error if user_id or task_id is missing or invalid

#### Cross-Cutting Requirements

- **FR-044**: All tools MUST be stateless - each invocation is independent
- **FR-045**: All tools MUST validate user_id matches the task owner before performing operations
- **FR-046**: All tools MUST return structured responses in a consistent format
- **FR-047**: All tools MUST handle database errors gracefully and return appropriate error messages
- **FR-048**: All tools MUST validate input types and ranges before processing
- **FR-049**: All tools MUST support Unicode characters in text fields (titles, descriptions)
- **FR-050**: All tools MUST complete execution within 3 seconds under normal conditions

### Key Entities

- **Task**: Represents a single todo item. Key attributes include:
  - `id` (integer, unique identifier, auto-generated)
  - `user_id` (integer, foreign key to user, required)
  - `title` (string, 1-500 chars, required)
  - `description` (string, 0-2000 chars, optional)
  - `completed` (boolean, default false)
  - `created_at` (timestamp, auto-generated)
  - `updated_at` (timestamp, auto-updated)

- **MCP Tool**: Represents a callable function that the AI agent can invoke. Key characteristics include:
  - Stateless operation (no memory between calls)
  - Input schema (typed parameters)
  - Output schema (structured response)
  - Error schema (standardized error format)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five MCP tools (add_task, list_tasks, complete_task, update_task, delete_task) are callable by the AI agent with documented schemas
- **SC-002**: Each tool call completes within 3 seconds for 95% of requests under normal database conditions
- **SC-003**: Tools correctly enforce user isolation - zero instances of users accessing other users' tasks
- **SC-004**: Input validation catches 100% of malformed requests before database operations
- **SC-005**: Error responses provide actionable information without exposing internal implementation details
- **SC-006**: Tools handle concurrent operations on the same task without data corruption
- **SC-007**: All tool calls are stateless - restarting the server does not affect tool behavior
- **SC-008**: Tools support at least 100 concurrent invocations without performance degradation
- **SC-009**: Tools correctly handle Unicode text in all languages without data loss or corruption
- **SC-010**: The AI agent can successfully complete all basic todo workflows (create, read, update, complete, delete) using only these five tools

### User Experience Outcomes

- **SC-011**: AI agent responses based on tool outputs feel natural and informative to users
- **SC-012**: Error messages from tools allow the AI agent to provide helpful guidance to users
- **SC-013**: Tool response times are fast enough that users perceive instant feedback (<3 seconds)
- **SC-014**: Tools provide sufficient information for the AI agent to maintain conversational context across multi-turn interactions

## Assumptions *(mandatory)*

- The AI agent has access to a valid user_id from the authenticated JWT token before invoking tools
- The database schema for tasks already exists with appropriate constraints and indexes
- Database connection pooling handles concurrent tool invocations efficiently
- The MCP server implementation will handle tool registration and schema validation
- The OpenAI Agents SDK correctly passes parameters to MCP tools according to schemas
- Task IDs are unique integers assigned by the database auto-increment mechanism
- Timestamps are stored in UTC and converted to user timezone only at presentation layer
- The system handles a maximum of 10,000 tasks per user without performance issues
- Network latency between the AI agent and MCP server is negligible (same process or local network)
- Database transactions ensure atomic operations for create, update, and delete operations

## Tool Schemas *(mandatory for this spec)*

### Tool: add_task

**Purpose**: Creates a new task for the specified user

**Input Parameters**:
```json
{
  "user_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the user creating the task"
  },
  "title": {
    "type": "string",
    "required": true,
    "minLength": 1,
    "maxLength": 500,
    "description": "The task title"
  },
  "description": {
    "type": "string",
    "required": false,
    "maxLength": 2000,
    "description": "Optional detailed description of the task"
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "task": {
    "id": 123,
    "user_id": 456,
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "completed": false,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T10:30:00Z"
  }
}
```

**Error Cases**:
- `user_id` missing: `{"success": false, "error": "user_id is required"}`
- `title` missing or empty: `{"success": false, "error": "title is required and cannot be empty"}`
- `title` exceeds 500 chars: `{"success": false, "error": "title must be 500 characters or less"}`
- `description` exceeds 2000 chars: `{"success": false, "error": "description must be 2000 characters or less"}`
- Database error: `{"success": false, "error": "Failed to create task. Please try again."}`

---

### Tool: list_tasks

**Purpose**: Retrieves all tasks for the specified user, optionally filtered by completion status

**Input Parameters**:
```json
{
  "user_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the user whose tasks to retrieve"
  },
  "completed": {
    "type": "boolean",
    "required": false,
    "description": "Filter by completion status (true=completed only, false=incomplete only, omit=all)"
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "tasks": [
    {
      "id": 123,
      "user_id": 456,
      "title": "Buy groceries",
      "description": "Milk, bread, eggs",
      "completed": false,
      "created_at": "2025-12-19T10:30:00Z",
      "updated_at": "2025-12-19T10:30:00Z"
    },
    {
      "id": 124,
      "user_id": 456,
      "title": "Call dentist",
      "description": null,
      "completed": true,
      "created_at": "2025-12-18T14:20:00Z",
      "updated_at": "2025-12-19T09:15:00Z"
    }
  ],
  "count": 2
}
```

**Error Cases**:
- `user_id` missing: `{"success": false, "error": "user_id is required"}`
- `completed` invalid type: `{"success": false, "error": "completed must be a boolean value"}`
- Database error: `{"success": false, "error": "Failed to retrieve tasks. Please try again."}`

---

### Tool: complete_task

**Purpose**: Marks a task as completed for the specified user

**Input Parameters**:
```json
{
  "user_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the user who owns the task"
  },
  "task_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the task to mark complete"
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "task": {
    "id": 123,
    "user_id": 456,
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "completed": true,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T11:45:00Z"
  }
}
```

**Error Cases**:
- `user_id` missing: `{"success": false, "error": "user_id is required"}`
- `task_id` missing: `{"success": false, "error": "task_id is required"}`
- Task not found or belongs to different user: `{"success": false, "error": "Task not found"}`
- Database error: `{"success": false, "error": "Failed to complete task. Please try again."}`

---

### Tool: update_task

**Purpose**: Updates the title and/or description of a task for the specified user

**Input Parameters**:
```json
{
  "user_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the user who owns the task"
  },
  "task_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the task to update"
  },
  "title": {
    "type": "string",
    "required": false,
    "minLength": 1,
    "maxLength": 500,
    "description": "New task title (if updating title)"
  },
  "description": {
    "type": "string",
    "required": false,
    "maxLength": 2000,
    "description": "New task description (if updating description, null to clear)"
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "task": {
    "id": 123,
    "user_id": 456,
    "title": "Buy groceries and milk",
    "description": "Milk, bread, eggs, and cheese",
    "completed": false,
    "created_at": "2025-12-19T10:30:00Z",
    "updated_at": "2025-12-19T12:00:00Z"
  }
}
```

**Error Cases**:
- `user_id` missing: `{"success": false, "error": "user_id is required"}`
- `task_id` missing: `{"success": false, "error": "task_id is required"}`
- No fields to update: `{"success": false, "error": "At least one field (title or description) must be provided"}`
- `title` empty or exceeds 500 chars: `{"success": false, "error": "title must be between 1 and 500 characters"}`
- `description` exceeds 2000 chars: `{"success": false, "error": "description must be 2000 characters or less"}`
- Task not found or belongs to different user: `{"success": false, "error": "Task not found"}`
- Database error: `{"success": false, "error": "Failed to update task. Please try again."}`

---

### Tool: delete_task

**Purpose**: Permanently deletes a task for the specified user

**Input Parameters**:
```json
{
  "user_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the user who owns the task"
  },
  "task_id": {
    "type": "integer",
    "required": true,
    "description": "The ID of the task to delete"
  }
}
```

**Output Format**:
```json
{
  "success": true,
  "message": "Task deleted successfully",
  "deleted_task_id": 123
}
```

**Error Cases**:
- `user_id` missing: `{"success": false, "error": "user_id is required"}`
- `task_id` missing: `{"success": false, "error": "task_id is required"}`
- Task not found or belongs to different user: `{"success": false, "error": "Task not found"}`
- Database error: `{"success": false, "error": "Failed to delete task. Please try again."}`

---

## Out of Scope

- Batch operations (creating, updating, or deleting multiple tasks in one call)
- Task search or filtering by title/description keywords
- Task sorting options beyond default creation date
- Task prioritization, categorization, or tagging
- Task due dates, reminders, or time-based operations
- Task ownership transfer between users
- Task sharing or collaboration features
- Soft delete or task archive functionality (delete is permanent)
- Task history or audit trail of changes
- Bulk export or import of tasks
- Task templates or recurring tasks
- Pagination for task lists (all tasks returned in single response)
- Rate limiting or quota enforcement (handled at API gateway level)
- Caching or performance optimization (stateless tools rely on database performance)

## Dependencies

- Database schema with tasks table including all required fields and constraints
- MCP SDK (Python) for tool registration and schema validation
- Database connection with appropriate permissions for CRUD operations
- OpenAI Agents SDK for invoking MCP tools
- Authentication layer providing valid user_id before tool invocation
- Error handling framework for consistent error response format

## Risks & Mitigations

1. **Risk**: Database performance degrades with large task lists (10,000+ tasks per user)
   - **Mitigation**: Implement database indexes on user_id and created_at fields. Monitor query performance and add pagination if needed (future scope).

2. **Risk**: Concurrent updates to the same task cause data conflicts or race conditions
   - **Mitigation**: Use database transactions with appropriate isolation levels. Last write wins strategy acceptable for this use case.

3. **Risk**: MCP tool schema changes break AI agent integration
   - **Mitigation**: Version the tool schemas and maintain backward compatibility. Document schema changes in release notes.

4. **Risk**: Error messages expose sensitive database internals or schema details
   - **Mitigation**: Sanitize all error messages before returning. Log detailed errors server-side but return generic messages to tools.

5. **Risk**: Tools fail to enforce user isolation due to implementation bugs
   - **Mitigation**: Implement comprehensive unit tests verifying user isolation for all operations. Include security testing in CI/CD pipeline.

6. **Risk**: Unicode or special characters in task text cause encoding issues
   - **Mitigation**: Ensure database uses UTF-8 encoding. Test with multilingual content during development.
