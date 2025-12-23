# Chat Endpoint API Specification

**Version**: 1.0.0
**Status**: Draft
**Created**: 2025-12-19
**Feature**: Phase III AI-Powered Todo Chatbot

## Overview

The Chat Endpoint enables natural language interaction between users and the AI-powered todo assistant. Users send conversational messages, and the system processes them to perform task management operations (create, view, update, complete, delete) while maintaining conversation history.

## Endpoint Definition

### Path and Method

```
POST /api/{user_id}/chat
```

**Path Parameters**:
- `user_id` (string, required): Unique identifier of the authenticated user

**HTTP Method**: POST

**Content-Type**: `application/json`

---

## Authentication

### Requirements

- **Authentication Type**: JWT Bearer Token
- **Header**: `Authorization: Bearer <jwt_token>`
- **Token Validation**: Required on every request
- **Token Claims**: Must include `user_id` that matches the path parameter
- **Shared Secret**: Backend validates JWT using `BETTER_AUTH_SECRET`

### Authentication Failure

If authentication fails, the endpoint returns:
- **Status Code**: 401 Unauthorized
- **Response Body**:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

### Authorization Failure

If the JWT `user_id` does not match the path `user_id`:
- **Status Code**: 403 Forbidden
- **Response Body**:
```json
{
  "error": "Forbidden",
  "message": "You can only access your own conversations"
}
```

---

## Request Schema

### Request Body

```json
{
  "conversation_id": <integer | null>,
  "message": <string>
}
```

### Field Definitions

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `conversation_id` | integer or null | Optional | ID of existing conversation to continue. If `null` or omitted, a new conversation is created. | Must belong to the authenticated user if provided |
| `message` | string | **Required** | User's natural language message | Min length: 1 character, Max length: 2000 characters |

### Request Validation Rules

- `message` field MUST NOT be empty or whitespace-only
- `message` MUST NOT exceed 2000 characters
- If `conversation_id` is provided, it MUST reference an existing conversation owned by the user
- If `conversation_id` is invalid or belongs to another user, return 404 Not Found

### Request Examples

**Example 1: Starting a New Conversation**
```json
{
  "message": "I need to buy groceries tomorrow"
}
```

**Example 2: Continuing an Existing Conversation**
```json
{
  "conversation_id": 123,
  "message": "What's on my list?"
}
```

**Example 3: Multi-turn Context**
```json
{
  "conversation_id": 123,
  "message": "Mark the first one as complete"
}
```

---

## Response Schema

### Success Response

**Status Code**: 200 OK

**Response Body**:
```json
{
  "conversation_id": <integer>,
  "response": <string>,
  "tool_calls": <array | null>
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | ID of the conversation (newly created or existing). Used for subsequent messages in the same conversation. |
| `response` | string | Natural language response from the AI assistant, confirming actions or answering questions. |
| `tool_calls` | array or null | Optional array of tool invocations made during processing. Each tool call contains `tool` (name) and `result` (structured output). May be `null` if no tools were called. |

### Tool Call Structure

When `tool_calls` is present, each element has:
```json
{
  "tool": <string>,
  "result": <object>
}
```

- `tool`: Name of the MCP tool invoked (e.g., "add_task", "list_tasks", "complete_task")
- `result`: Structured result returned by the tool

### Response Examples

**Example 1: Task Creation**
```json
{
  "conversation_id": 123,
  "response": "I've added 'Buy groceries tomorrow' to your task list.",
  "tool_calls": [
    {
      "tool": "add_task",
      "result": {
        "id": 456,
        "title": "Buy groceries tomorrow",
        "completed": false,
        "created_at": "2025-12-19T10:30:00Z"
      }
    }
  ]
}
```

**Example 2: Listing Tasks**
```json
{
  "conversation_id": 123,
  "response": "Here's what you need to do:\n1. Buy groceries tomorrow\n2. Call the dentist at 3pm\n3. Finish project report",
  "tool_calls": [
    {
      "tool": "list_tasks",
      "result": {
        "tasks": [
          {"id": 456, "title": "Buy groceries tomorrow", "completed": false},
          {"id": 457, "title": "Call the dentist at 3pm", "completed": false},
          {"id": 458, "title": "Finish project report", "completed": false}
        ]
      }
    }
  ]
}
```

**Example 3: Conversational Response (No Tools)**
```json
{
  "conversation_id": 123,
  "response": "Hello! I'm your AI assistant. I can help you manage tasks. Just tell me what you need to do!",
  "tool_calls": null
}
```

**Example 4: Task Completion**
```json
{
  "conversation_id": 123,
  "response": "Great! I've marked 'Buy groceries tomorrow' as complete.",
  "tool_calls": [
    {
      "tool": "complete_task",
      "result": {
        "id": 456,
        "title": "Buy groceries tomorrow",
        "completed": true,
        "updated_at": "2025-12-19T11:00:00Z"
      }
    }
  ]
}
```

**Example 5: Ambiguity Handling**
```json
{
  "conversation_id": 123,
  "response": "I found 3 tasks related to 'report'. Which one did you mean?\n1. Finish project report\n2. Submit quarterly report\n3. Review expense report",
  "tool_calls": [
    {
      "tool": "list_tasks",
      "result": {
        "tasks": [
          {"id": 458, "title": "Finish project report", "completed": false},
          {"id": 459, "title": "Submit quarterly report", "completed": false},
          {"id": 460, "title": "Review expense report", "completed": false}
        ]
      }
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request

Returned when request validation fails.

**Response Body**:
```json
{
  "error": "Bad Request",
  "message": <string>,
  "details": <object | null>
}
```

**Common Scenarios**:
- Missing `message` field
- Empty or whitespace-only `message`
- `message` exceeds 2000 characters
- Invalid JSON format

**Example**:
```json
{
  "error": "Bad Request",
  "message": "Message field is required and cannot be empty",
  "details": null
}
```

### 401 Unauthorized

Returned when JWT token is missing, invalid, or expired.

**Response Body**:
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

### 403 Forbidden

Returned when authenticated user attempts to access another user's conversation.

**Response Body**:
```json
{
  "error": "Forbidden",
  "message": "You can only access your own conversations"
}
```

### 404 Not Found

Returned when `conversation_id` references a non-existent or unauthorized conversation.

**Response Body**:
```json
{
  "error": "Not Found",
  "message": "Conversation not found or you don't have access to it",
  "details": {
    "conversation_id": 999
  }
}
```

### 500 Internal Server Error

Returned when an unexpected error occurs during processing.

**Response Body**:
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred. Please try again later."
}
```

**Note**: Specific error details MUST NOT be exposed to clients to prevent information leakage.

### 503 Service Unavailable

Returned when AI service or database is temporarily unavailable.

**Response Body**:
```json
{
  "error": "Service Unavailable",
  "message": "The AI assistant is temporarily unavailable. Please try again in a moment."
}
```

---

## Stateless Behavior Guarantees

### Core Principle

The Chat Endpoint is **completely stateless**. The server maintains **NO** in-memory conversation state, user session data, or request context between API calls.

### Statelessness Requirements

1. **No Server-Side Sessions**
   - Every request is independent and self-contained
   - Server does not maintain session variables or in-memory cache
   - Multiple servers can handle requests from the same user without coordination

2. **Database as State Authority**
   - All conversation history is retrieved from the database on every request
   - All messages (user and assistant) are persisted to the database before responding
   - No state survives server restarts - everything is reconstructed from database

3. **Request Independence**
   - Each request MUST include all necessary context (`user_id`, `conversation_id`, `message`)
   - Requests can be processed in any order without affecting correctness
   - No assumptions about previous requests in the same conversation

4. **Horizontal Scalability**
   - Any server instance can handle any request for any user
   - No sticky sessions or server affinity required
   - Load balancers can route freely across instances

5. **Conversation Reconstruction**
   - On each request, the system:
     1. Authenticates the user via JWT
     2. Retrieves conversation history from database (if `conversation_id` provided)
     3. Processes the new message with full context
     4. Stores the new user message and assistant response
     5. Returns the response
   - This entire flow is atomic per request

### Stateless Workflow Example

**Request 1**:
```
POST /api/user123/chat
{ "message": "Add buy milk" }
```
- Server creates new conversation in database (ID: 1)
- Server creates user message in database
- Server processes with AI, calls `add_task` tool
- Server creates assistant message in database
- Server returns `conversation_id: 1`

**Request 2** (different server instance):
```
POST /api/user123/chat
{ "conversation_id": 1, "message": "What's on my list?" }
```
- Server retrieves conversation 1 history from database
- Server creates new user message in database
- Server processes with full context, calls `list_tasks` tool
- Server creates assistant message in database
- Server returns response

**Server Restart**: No data lost; all state is in database.

---

## Performance Expectations

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time (p95) | < 3 seconds | Time from request received to response sent |
| Database Query Time | < 500ms | Time to fetch conversation history |
| Concurrent Users | 100+ | Number of simultaneous active conversations |
| Message Throughput | 50+ msg/sec | System-wide message processing capacity |

---

## Data Isolation Guarantees

### User Data Separation

- Each user can ONLY access their own conversations and tasks
- `conversation_id` MUST be validated against authenticated `user_id`
- Database queries MUST include `user_id` filter to prevent cross-user data leakage

### Security Requirements

- All requests MUST use HTTPS in production
- JWT tokens MUST NOT be logged
- User messages MUST NOT be logged in plaintext (only stored in database)
- Error messages MUST NOT reveal system internals or other users' data

---

## Idempotency and Reliability

### Idempotency

This endpoint is **NOT idempotent** by design:
- Each identical request creates a new message in the conversation
- Duplicate submissions (e.g., network retry) may result in duplicate messages
- Clients SHOULD implement retry logic with caution to avoid duplicate task creation

**Recommendation**: Clients should display a loading state and disable submission during processing to prevent accidental duplicates.

### Retry Behavior

- **5xx errors**: Clients MAY retry after exponential backoff
- **4xx errors** (except 429): Clients SHOULD NOT retry without correction
- **429 Rate Limit**: Clients SHOULD respect `Retry-After` header

---

## Rate Limiting

### Limits (Optional, Implementation-Dependent)

- **Per User**: 60 requests per minute
- **Response Header**: `X-RateLimit-Remaining: <count>`
- **Exceeded Response**:
  - **Status Code**: 429 Too Many Requests
  - **Header**: `Retry-After: <seconds>`
  - **Body**:
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please try again in 30 seconds."
}
```

---

## Versioning

### Current Version

- **Version**: 1.0.0
- **Path**: `/api/{user_id}/chat` (no version in path for v1)

### Future Versioning Strategy

- Breaking changes will introduce `/api/v2/{user_id}/chat`
- v1 will be maintained for backward compatibility during migration period
- Deprecation notices will be communicated 90 days in advance

---

## Contract Summary

This API contract guarantees:

✅ **Stateless**: No server-side session or in-memory state
✅ **Authenticated**: JWT required and validated on every request
✅ **Isolated**: Users can only access their own data
✅ **Conversational**: Natural language input/output
✅ **Persistent**: All data stored in database before responding
✅ **Scalable**: Horizontal scaling supported without coordination
✅ **Resilient**: Server restarts do not lose data

---

## Related Documentation

- **Feature Spec**: `specs/001-chatbot/spec.md`
- **Constitution**: `.specify/memory/constitution.md`
- **MCP Tools Spec**: To be defined in separate document
- **Database Schema**: To be defined in implementation plan
