# Agent Orchestrator Architecture

## Overview

The Agent Orchestrator is the brain of the Todo Chatbot. It coordinates conversation management, OpenAI agent processing, MCP tool invocation, and response generation in a stateless architecture. Every request is independent, fetching conversation history from the database, processing with the AI agent, storing results, and returning responses.

## Request-Response Flow

### 1. Request Reception

**Endpoint**: POST /api/{user_id}/chat

**Request Structure**:
```json
{
  "conversation_id": 123,  // optional - creates new if not provided
  "message": "add task to buy groceries"
}
```

**Processing Steps**:
1. Extract `user_id` from JWT token claims
2. Validate path `user_id` matches JWT `user_id` (403 if mismatch)
3. If `conversation_id` provided:
   - Verify conversation exists and belongs to user (404 if not found, 403 if wrong user)
4. If `conversation_id` not provided:
   - Create new conversation record (INSERT into conversations table)
   - Get new `conversation_id` from database

### 2. Context Retrieval

**Database Queries**:
```sql
-- Query 1: Get conversation metadata
SELECT id, user_id, created_at, updated_at
FROM conversations
WHERE id = ? AND user_id = ?;

-- Query 2: Get recent messages (last 20)
SELECT id, role, content, created_at
FROM messages
WHERE conversation_id = ?
ORDER BY created_at ASC
LIMIT 20;
```

**Context Window Strategy**:
- Include last 20 messages (configurable via MAX_CONVERSATION_HISTORY env var)
- If total tokens > 4000, truncate older messages (keep most recent)
- Always include system prompt (not stored in database, defined in code)
- Format messages for OpenAI API (array of {role, content} objects)

**Message Formatting**:
```python
# Conceptual structure
formatted_messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "add task to buy groceries"},
    {"role": "assistant", "content": "I've added 'Buy groceries' to your task list."},
    {"role": "user", "content": message}  # Current user message
]
```

### 3. Agent Processing

**OpenAI Agents SDK Configuration**:
```python
# Conceptual configuration
agent = Agent(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    system_prompt=SYSTEM_PROMPT,
    tools=[
        add_task_tool,
        list_tasks_tool,
        complete_task_tool,
        update_task_tool,
        delete_task_tool
    ]
)

# Process request
response = agent.run(
    conversation_history=formatted_messages,
    user_id=user_id  # Passed to all tool calls
)
```

**Agent Responsibilities**:
1. Analyze user message for intent (create task, list tasks, complete task, etc.)
2. Determine which MCP tool(s) to invoke (if any)
3. Extract parameters from natural language ("buy groceries" → title="Buy groceries")
4. Invoke MCP tools via registered tool functions
5. Receive tool results (success data or error messages)
6. Generate natural language response based on tool results and conversation context

### 4. Tool Invocation

**Tool Call Workflow**:

**Step 1**: Agent generates tool call request
```python
# Agent decides to call add_task
tool_call = {
    "tool": "add_task",
    "parameters": {
        "user_id": 123,  # Injected by orchestrator, not extracted from user message
        "title": "Buy groceries",
        "description": None  # Optional, not provided in this example
    }
}
```

**Step 2**: Orchestrator validates and invokes MCP tool
```python
# Validation
if tool_call["parameters"]["user_id"] != authenticated_user_id:
    raise AuthorizationError("user_id mismatch")

# MCP tool invocation
result = await mcp_client.call_tool(
    tool_name=tool_call["tool"],
    parameters=tool_call["parameters"]
)
```

**Step 3**: Tool returns result or error
```python
# Success
{
    "success": True,
    "task": {
        "id": 456,
        "user_id": 123,
        "title": "Buy groceries",
        "description": None,
        "completed": False,
        "created_at": "2025-12-19T10:30:00Z",
        "updated_at": "2025-12-19T10:30:00Z"
    }
}

# Error
{
    "success": False,
    "error": "ValidationError",
    "message": "Title must be between 1 and 200 characters"
}
```

**Step 4**: Result provided to agent for response generation

### 5. Response Generation

**Agent Generates Response**:

**Success Case**:
```json
{
  "response": "I've added 'Buy groceries' to your task list.",
  "tool_calls": [
    {
      "tool": "add_task",
      "result": {
        "task_id": 456,
        "title": "Buy groceries",
        "completed": false
      }
    }
  ]
}
```

**Error Case** (Tool Failure):
```json
{
  "response": "I couldn't add that task because the title is too long. Task titles must be 200 characters or less.",
  "tool_calls": [
    {
      "tool": "add_task",
      "error": "ValidationError"
    }
  ]
}
```

**No Tool Case** (Conversational):
```json
{
  "response": "Hello! I'm your task management assistant. I can help you create, view, complete, update, and delete tasks. What would you like to do?",
  "tool_calls": []
}
```

### 6. State Persistence

**Database Writes** (in transaction):

```sql
-- Step 1: Store user message
INSERT INTO messages (conversation_id, user_id, role, content, created_at)
VALUES (?, ?, 'user', ?, CURRENT_TIMESTAMP)
RETURNING id;

-- Step 2: Store assistant response
INSERT INTO messages (conversation_id, user_id, role, content, created_at)
VALUES (?, ?, 'assistant', ?, CURRENT_TIMESTAMP)
RETURNING id;

-- Step 3: Update conversation timestamp
UPDATE conversations
SET updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
```

**Transaction Behavior**:
- All 3 operations succeed or all fail (atomic)
- If database write fails, return 500 error (don't return response to user if it won't be saved)
- If OpenAI agent fails but user message already stored, still save error response

### 7. Response Return to Client

**HTTP Response Structure**:
```json
{
  "conversation_id": 123,
  "response": "I've added 'Buy groceries' to your task list.",
  "tool_calls": [
    {
      "tool": "add_task",
      "result": {"task_id": 456, "title": "Buy groceries"}
    }
  ],
  "created_at": "2025-12-19T10:30:05Z"
}
```

**Status Codes**:
- 200 OK: Successful response (even if tool failed - agent handled it gracefully)
- 400 Bad Request: Invalid request (missing message, message too long)
- 401 Unauthorized: Invalid or expired JWT
- 403 Forbidden: user_id mismatch or conversation access violation
- 404 Not Found: conversation_id doesn't exist
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Database failure, OpenAI API failure, unexpected error

---

## System Prompt Design

### Purpose
Define agent personality, capabilities, and behavior to ensure natural, helpful, and accurate task management assistance.

### System Prompt Template

```
You are a helpful task management assistant that helps users manage their todo list through natural conversation.

CAPABILITIES:
- Create tasks when users express intentions or needs (e.g., "I need to buy groceries", "remind me to call dentist")
- Show task lists when requested (e.g., "what's on my list?", "show my tasks")
- Mark tasks complete when users indicate completion (e.g., "done with groceries", "finished the report")
- Update task details when users request changes (e.g., "change groceries to buy groceries and milk")
- Delete tasks when users want to remove them (e.g., "delete the dentist task", "remove task 3")

BEHAVIOR GUIDELINES:
- Always confirm actions with natural, conversational language (not robotic or technical)
- When creating tasks, extract key information (title, optional description) from user's message
- If user intent is ambiguous or multiple tasks match a description, ask clarifying questions
- Be friendly but concise - avoid unnecessary verbosity or over-explanation
- When listing tasks, format them in a clear, numbered or bulleted format
- Handle errors gracefully - never expose technical details or stack traces to users
- If a requested task doesn't exist, kindly explain and offer alternatives (show list, create new task)

TOOL USAGE:
- Call add_task when users express a new todo item, need, or intention
- Call list_tasks when users ask to see their tasks (all, pending, or completed)
- Call complete_task when users indicate they've finished a task
- Call update_task when users want to modify a task's title or description
- Call delete_task when users want to remove a task

IMPORTANT RULES:
- The user_id parameter is automatically provided - never ask users for their ID
- Never make up task IDs - always use IDs returned from list_tasks tool
- When users refer to "task 1" or "the first task", list tasks first to get the actual ID
- If a task doesn't exist, don't fail silently - explain kindly and offer to help
- When multiple tasks match a description, list them and ask which one the user means
- Preserve user privacy - never mention other users or reference user IDs in responses

RESPONSE EXAMPLES:
- Task created: "I've added 'Buy groceries' to your task list."
- Task completed: "Great! I've marked 'Buy groceries' as complete."
- Task deleted: "I've removed 'Call dentist' from your list."
- Task updated: "I've updated your task to 'Buy groceries and milk'."
- Task not found: "I couldn't find a task matching 'report'. Would you like me to show your task list or create a new task?"
- Ambiguous request: "I found 3 tasks about 'report'. Which one did you mean? (1) Write quarterly report, (2) Submit expense report, (3) Review team report"
- List tasks: "Here are your pending tasks: 1. Buy groceries 2. Call dentist 3. Finish project report"
```

---

## Tool Integration Patterns

### Tool Registration

**Available MCP Tools**:
1. **add_task** - Creates new task for user
2. **list_tasks** - Retrieves user's tasks with optional filtering (all, pending, completed)
3. **complete_task** - Marks task as completed
4. **update_task** - Modifies task title and/or description
5. **delete_task** - Permanently removes task

**Registration Format**:
```python
# Conceptual - OpenAI Agents SDK tool registration
tools = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title (1-200 chars)"},
                    "description": {"type": "string", "description": "Optional task details"}
                },
                "required": ["title"]
            }
        },
        "handler": add_task_mcp_tool  # Reference to MCP tool function
    },
    # ... other tools
]
```

### Tool Call Sequence Examples

**Example 1: Create Single Task**

**User Message**: "I need to buy groceries"

**Agent Processing**:
1. Detects intent: Create task
2. Extracts parameters: title="Buy groceries"
3. Plans tool call: add_task(user_id=123, title="Buy groceries")
4. Executes tool call via MCP
5. Receives result: task_id=456
6. Generates response: "I've added 'Buy groceries' to your task list."

**Example 2: Create Multiple Tasks**

**User Message**: "add task to buy groceries and call the dentist"

**Agent Processing**:
1. Detects intent: Create 2 tasks
2. Plans tool calls:
   - add_task(user_id=123, title="Buy groceries")
   - add_task(user_id=123, title="Call the dentist")
3. Executes both tool calls sequentially
4. Receives results: task_id=456 and task_id=457
5. Generates response: "I've added two tasks to your list: 'Buy groceries' and 'Call the dentist'."

**Example 3: List Tasks**

**User Message**: "what do I need to do?"

**Agent Processing**:
1. Detects intent: List pending tasks
2. Plans tool call: list_tasks(user_id=123, filter="pending")
3. Executes tool call
4. Receives result: array of 3 pending tasks
5. Generates response: "Here are your pending tasks:\n1. Buy groceries\n2. Call the dentist\n3. Finish project report"

**Example 4: Complete Task by Reference**

**User Message**: "done with groceries"

**Agent Processing**:
1. Detects intent: Complete task
2. Needs task_id but only has title reference
3. Plans sequence:
   - list_tasks(user_id=123, filter="pending")
   - Find task matching "groceries"
   - complete_task(user_id=123, task_id=456)
4. Executes sequence
5. Generates response: "Great! I've marked 'Buy groceries' as complete."

**Example 5: Ambiguous Reference**

**User Message**: "delete the report"

**Agent Processing**:
1. Detects intent: Delete task
2. Plans tool call: list_tasks(user_id=123)
3. Finds multiple matches: "Write quarterly report", "Submit expense report", "Review team report"
4. Generates response: "I found 3 tasks about 'report'. Which one did you mean?\n1. Write quarterly report\n2. Submit expense report\n3. Review team report\n\nPlease let me know the number or be more specific."

---

## Error Handling Strategy

### Error Categories

#### 1. Tool Execution Errors

**Scenario**: MCP tool returns error (validation failure, not found, authorization failure)

**Handling**:
```python
if tool_result["success"] == False:
    error_type = tool_result["error"]
    error_message = tool_result["message"]
    # Agent receives error and converts to natural language
    # Don't expose technical error types to user
```

**Example Responses**:
- ValidationError (title too long): "I couldn't add that task because the title is too long. Task titles must be 200 characters or less."
- NotFoundError (task doesn't exist): "I couldn't find a task matching 'pizza'. Could you be more specific or would you like me to show your task list?"
- AuthorizationError (accessing other user's task): "I can only access your tasks. Please make sure you're referring to one of your own tasks."

#### 2. AI Service Errors

**Scenario**: OpenAI API failure (rate limit, timeout, service unavailable, invalid API key)

**Handling**:
```python
try:
    response = await openai_agent.run(messages)
except OpenAIRateLimitError:
    return error_response("I'm experiencing high demand right now. Please try again in a moment.")
except OpenAITimeoutError:
    return error_response("The request took too long. Please try again.")
except OpenAIServiceUnavailableError:
    return error_response("I'm temporarily unavailable. Please try again shortly.")
except OpenAIAuthenticationError:
    # Log critical error - this shouldn't happen in production
    return error_response("Service configuration error. Please contact support.")
```

**Retry Logic**:
- Rate limit: Don't retry immediately (return 429 to client)
- Timeout: Retry once with extended timeout
- Service unavailable: Retry once after 2 seconds
- Authentication error: Don't retry (configuration issue)

#### 3. Database Errors

**Scenario**: Connection failure, query timeout, constraint violation, transaction rollback

**Handling**:
```python
try:
    async with database.transaction():
        # Store messages, update conversation
except DatabaseConnectionError:
    # Retry once after reconnecting
except DatabaseTimeoutError:
    return error_response("The database is responding slowly. Please try again.")
except DatabaseConstraintViolationError as e:
    # Log the specific constraint violation
    return error_response("Unable to save message due to data constraint.")
```

**Critical Rule**: Never return success response to user if database write failed. User must know their message wasn't saved.

#### 4. Validation Errors

**Scenario**: Invalid user_id, conversation_id mismatch, malformed request, message too long

**Handling**:
```python
# Input validation before processing
if not message or len(message) > 10000:
    return 400, {"error": "ValidationError", "message": "Message must be 1-10000 characters"}

if conversation_id and not conversation_belongs_to_user(conversation_id, user_id):
    return 403, {"error": "Forbidden", "message": "Cannot access this conversation"}
```

**Response**: Return 400 Bad Request with clear error message (no processing attempted)

#### 5. Authentication Errors

**Scenario**: Missing JWT, invalid signature, expired token, user_id mismatch

**Handling**:
```python
# Middleware handles JWT validation
if not jwt_token:
    return 401, {"error": "Unauthorized", "message": "Authentication required"}

if jwt_expired:
    return 401, {"error": "Unauthorized", "message": "Token expired. Please log in again."}

if path_user_id != jwt_user_id:
    return 403, {"error": "Forbidden", "message": "Cannot access other users' data"}
```

**Response**: Return 401 Unauthorized or 403 Forbidden (no processing attempted)

---

## Context Management

### History Retrieval Strategy

**Goal**: Provide enough context for agent to understand references without exceeding token limits

**Configuration**:
```bash
MAX_CONVERSATION_HISTORY=20  # Default: last 20 messages
MAX_CONVERSATION_TOKENS=4000  # Maximum tokens for conversation history
```

**Retrieval Query**:
```sql
SELECT id, role, content, created_at
FROM messages
WHERE conversation_id = ?
ORDER BY created_at DESC
LIMIT ?;  -- MAX_CONVERSATION_HISTORY
```

**Token Budget Calculation**:
```python
# Conceptual token counting
system_prompt_tokens = count_tokens(SYSTEM_PROMPT)  # ~300 tokens
tool_schema_tokens = count_tokens(tool_schemas)  # ~700 tokens
current_message_tokens = count_tokens(user_message)  # varies
response_budget = 500  # Reserve for agent response

available_for_history = 4000 - (system_prompt_tokens + tool_schema_tokens + current_message_tokens + response_budget)

if history_tokens > available_for_history:
    # Truncate older messages, keep most recent
    truncate_history(available_tokens=available_for_history)
```

### Message Formatting

**OpenAI API Format**:
```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "add task to buy groceries"},
    {"role": "assistant", "content": "I've added 'Buy groceries' to your task list."},
    {"role": "user", "content": "what's on my list?"},
    {"role": "assistant", "content": "Here are your pending tasks:\n1. Buy groceries"},
    {"role": "user", "content": current_user_message}
]
```

**Role Attribution**:
- System prompt: role="system" (always first, only one system message)
- User messages: role="user"
- Assistant responses: role="assistant"
- No other roles used (no "function" role for tool calls - handled internally by SDK)

---

## Security and Isolation

### User Authentication Flow

1. Client sends JWT in `Authorization: Bearer {token}` header
2. Backend middleware extracts token
3. Validate JWT signature using BETTER_AUTH_SECRET
4. Check expiration (exp claim < current time → 401)
5. Extract user_id from JWT claims
6. Store user_id in request context
7. Use user_id for all database queries and MCP tool calls

### Data Isolation Enforcement

**Database Queries**:
```sql
-- Conversations: Always filter by user_id
SELECT * FROM conversations WHERE id = ? AND user_id = ?;

-- Messages: Always join conversation and filter by user_id
SELECT m.* FROM messages m
JOIN conversations c ON m.conversation_id = c.id
WHERE c.id = ? AND c.user_id = ?;

-- Tasks (via MCP): All MCP tools require user_id parameter
-- MCP tools query: WHERE id = ? AND user_id = ?
```

**Critical Rule**: NEVER query by ID alone. Always include user_id filter.

### Input Sanitization

**User Messages**:
```python
# Escape HTML to prevent XSS
import html
sanitized_message = html.escape(user_message)

# Check for null bytes (security risk)
if '\x00' in user_message:
    return 400, {"error": "ValidationError", "message": "Invalid characters in message"}

# Length validation
if len(user_message) < 1 or len(user_message) > 10000:
    return 400, {"error": "ValidationError", "message": "Message must be 1-10000 characters"}
```

**Tool Parameters**:
```python
# Validate types before passing to MCP tools
if not isinstance(task_id, int):
    return 400, {"error": "ValidationError", "message": "task_id must be an integer"}

# Validate ranges
if task_id < 1:
    return 400, {"error": "ValidationError", "message": "task_id must be positive"}
```

### Rate Limiting

**Per-User Limits**:
```python
# Redis-based rate limiting (or in-memory for development)
RATE_LIMITS = {
    "messages_per_hour": 100,
    "messages_per_minute": 20,
    "tool_calls_per_conversation": 50  # Prevent runaway loops
}

# Check before processing
if user_message_count_last_hour >= 100:
    return 429, {
        "error": "RateLimitExceeded",
        "message": "Too many requests. Please try again later.",
        "retry_after": seconds_until_limit_resets
    }
```

---

## Performance Considerations

### Response Time Targets

- **p50**: < 1 second (from HTTP request to response)
- **p95**: < 3 seconds (constitution requirement)
- **p99**: < 5 seconds
- **timeout**: 45 seconds (request times out and returns 504)

### Optimization Strategies

#### 1. Parallel Processing

```python
# Fetch conversation and messages in parallel
conversation_task = asyncio.create_task(get_conversation(conversation_id, user_id))
messages_task = asyncio.create_task(get_messages(conversation_id, limit=20))

conversation, messages = await asyncio.gather(conversation_task, messages_task)
```

#### 2. Connection Pooling

```python
# Database connection pool
DATABASE_POOL_SIZE = 10  # Max concurrent connections
DATABASE_POOL_TIMEOUT = 5  # Seconds to wait for available connection

# OpenAI SDK uses built-in HTTP/2 connection pooling (no configuration needed)
```

#### 3. Timeout Limits

```python
TIMEOUTS = {
    "openai_api": 30,  # OpenAI agent processing timeout
    "database_query": 5,  # Individual query timeout
    "mcp_tool": 10,  # MCP tool call timeout
    "total_request": 45  # Overall request timeout
}
```

#### 4. Caching (Stateless-Safe Only)

**What CAN be cached**:
- System prompt (doesn't change per request)
- Tool schemas (doesn't change per request)
- Database connection (connection pooling)

**What CANNOT be cached** (violates stateless principle):
- Conversation history (must fetch fresh on every request)
- User data (tasks, messages)
- Authentication state (verify JWT on every request)

---

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o  # or gpt-4o-mini for cost savings
OPENAI_TEMPERATURE=0.7  # 0.0 = deterministic, 1.0 = creative
OPENAI_TIMEOUT_SECONDS=30

# Agent Configuration
MAX_CONVERSATION_HISTORY=20  # Messages to include in context
MAX_TOOL_CALLS_PER_REQUEST=5  # Prevent runaway agent loops
SYSTEM_PROMPT_VERSION=v1  # For A/B testing different prompts

# MCP Configuration
MCP_SERVER_URL=http://localhost:8001
MCP_TIMEOUT_SECONDS=10

# Database Configuration
DATABASE_URL=postgresql://user:pass@neon.tech:5432/db
DB_POOL_SIZE=10
DB_TIMEOUT_SECONDS=5

# Authentication
BETTER_AUTH_SECRET=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_MESSAGES_PER_HOUR=100
RATE_LIMIT_MESSAGES_PER_MINUTE=20
```

### Feature Flags

```bash
# Experimental Features
ENABLE_MULTI_TURN_CONTEXT=true  # Use conversation history (recommended: true)
ENABLE_TOOL_CALLING=true  # Allow MCP tool invocation (required: true)
ENABLE_STREAMING=false  # Stream responses (future feature)
ENABLE_DEBUG_LOGGING=false  # Log all agent decisions (development only)
```

---

## Testing Strategy

### Unit Tests

**Test Coverage**:
- System prompt parsing and validation
- Message formatting for OpenAI API
- Context window truncation logic
- Error handling for each error category
- Input validation (message length, conversation_id, user_id)

**Example Test**:
```python
def test_format_messages_for_openai():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"}
    ]
    formatted = format_messages(messages, system_prompt=SYSTEM_PROMPT, current_message="new message")

    assert formatted[0]["role"] == "system"
    assert formatted[1]["role"] == "user"
    assert formatted[-1]["content"] == "new message"
```

### Integration Tests

**Test Scenarios**:
- Full request-response cycle with mock MCP tools
- Conversation history retrieval and formatting
- Tool call validation and error handling
- Database transaction rollback on errors
- JWT validation in middleware

**Example Test**:
```python
async def test_chat_endpoint_creates_task():
    # Arrange
    jwt_token = create_test_jwt(user_id=123)
    request_body = {"message": "add task to buy groceries"}

    # Act
    response = await client.post(
        "/api/123/chat",
        json=request_body,
        headers={"Authorization": f"Bearer {jwt_token}"}
    )

    # Assert
    assert response.status_code == 200
    assert "Buy groceries" in response.json()["response"]
    assert response.json()["tool_calls"][0]["tool"] == "add_task"
```

### End-to-End Tests

**Test Flows**:
- User creates task → verify in database
- User lists tasks → verify correct tasks returned
- User completes task → verify status updated
- User deletes task → verify task removed
- Multi-turn conversation → verify context maintained
- Error scenarios:
  - OpenAI API failure → graceful fallback message
  - MCP tool error → natural error message to user
  - Invalid user_id → 401 response
  - Conversation access violation → 403 response

---

## Architecture Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Web Frontend)                    │
│                  (OpenAI ChatKit Interface)                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ POST /api/{user_id}/chat
                             │ Authorization: Bearer {JWT}
                             │
┌────────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (Orchestrator)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. JWT Validation & user_id extraction               │   │
│  │    - Verify signature, expiration, issuer            │   │
│  │    - Extract user_id from claims                     │   │
│  │    - Validate path user_id matches JWT user_id       │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │ 2. Fetch Conversation + Messages from Database       │   │
│  │    - Get conversation by id + user_id                │   │
│  │    - Get last 20 messages ordered by created_at      │   │
│  │    - Parallel queries for performance                │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │ 3. Format Context for OpenAI Agent                   │   │
│  │    - System prompt + conversation history            │   │
│  │    - Truncate if exceeds token budget               │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │ 4. Invoke OpenAI Agent (via Agents SDK)              │   │
│  │    - Send formatted messages                         │   │
│  │    - Agent analyzes intent from natural language     │   │
│  │    - Agent calls MCP tools (if needed)               │   │
│  │    - Agent receives tool results                     │   │
│  │    - Agent generates natural language response       │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ├──────────────┐                     │
│                         │              │ (if tool calls)     │
│  ┌──────────────────────▼────────┐ ┌───▼──────────────┐     │
│  │ 5a. Generate Response         │ │ 5b. Call MCP Tools│     │
│  │     (no tools needed)         │ │   - add_task      │     │
│  │     - Conversational reply    │ │   - list_tasks    │     │
│  └──────────────────────┬────────┘ │   - complete_task │     │
│                         │          │   - update_task   │     │
│                         │          │   - delete_task   │     │
│                         │          └────┬──────────────┘     │
│                         │               │                    │
│                         │  ┌────────────▼────────────┐       │
│                         │  │ Tool results returned   │       │
│                         │  │ to agent for response   │       │
│                         │  │ generation              │       │
│                         │  └────────────┬────────────┘       │
│                         │               │                    │
│  ┌──────────────────────▼───────────────▼─────────────┐     │
│  │ 6. Store Messages in Database (Transaction)        │     │
│  │    - User message (role="user")                    │     │
│  │    - Assistant response (role="assistant")         │     │
│  │    - Update conversation.updated_at                │     │
│  │    - All succeed or all fail (atomic)              │     │
│  └──────────────────────┬───────────────────────────┘       │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │ 7. Return Response to Client                         │   │
│  │    {conversation_id, response, tool_calls, ...}      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼─────────┐       ┌───────────▼──────────┐
│  Neon PostgreSQL  │       │    MCP Server        │
│  - conversations  │       │  (Task Management    │
│  - messages       │       │   Tools)             │
│  - tasks          │       │  - add_task          │
│  - users          │       │  - list_tasks        │
└───────────────────┘       │  - complete_task     │
                            │  - update_task       │
                            │  - delete_task       │
                            └──────────────────────┘
```

---

## Design Principles

### Statelessness
- **No In-Memory State**: Every request is independent
- **Database as Source of Truth**: All state persisted to Neon PostgreSQL
- **Scalability**: Multiple orchestrator instances can run in parallel without coordination
- **Resilience**: Server restart doesn't lose conversation context

### Conversational-First
- **Natural Language**: Users never see technical details or command syntax
- **Intent Detection**: AI infers user intent from conversational input
- **Confirmation**: Always acknowledge actions with friendly, natural responses
- **Error Recovery**: Guide users to success, don't just report errors

### MCP Tool Architecture
- **Tool Abstraction**: Orchestrator doesn't know database schema details
- **Single Responsibility**: Each tool does one thing well
- **User Isolation**: Tools enforce user_id filtering
- **Error Transparency**: Tools return structured errors that agent can interpret

### Security by Design
- **Authentication Required**: JWT validation on every request (except /health)
- **Authorization Enforced**: User can only access their own data
- **Input Validation**: Sanitize all user input before processing
- **Audit Logging**: Log all tool calls, errors, and security events

---

## Implementation Checklist

Before considering the orchestrator design complete, verify:

- [x] Request-response flow fully documented (7 steps)
- [x] Tool integration pattern clear (registration, invocation, error handling)
- [x] Error handling covers all scenarios (5 categories)
- [x] Security and isolation requirements specified (authentication, authorization, sanitization, rate limiting)
- [x] Performance targets defined (< 3s p95 response time)
- [x] Configuration options documented (environment variables, feature flags)
- [x] System prompt provides clear agent guidance (capabilities, behavior, tool usage, rules, examples)
- [x] Context management strategy handles token limits (20 messages, 4000 tokens, truncation)
- [x] Testing strategy covers unit, integration, and E2E
- [x] Architecture diagram shows all components and data flows

---

## Success Criteria

The orchestrator design is complete when:

1. ✅ **Implementation Team Can Build**: Developers can implement without asking clarifying questions
2. ✅ **All Paths Documented**: Normal flow + all error scenarios covered
3. ✅ **Security Verified**: User isolation and authentication fully specified
4. ✅ **Performance Targets Set**: < 3s p95 response time defined
5. ✅ **Testable**: Clear test cases for each component
6. ✅ **Constitution Compliant**: Follows all Phase III principles (stateless, conversational-first, MCP tools, database as source of truth, authentication, AI agent integration)

---

**This orchestrator is the brain of the chatbot. It coordinates conversation management, AI processing, tool calling, and response generation. Every decision prioritizes user experience, security, and scalability.**
