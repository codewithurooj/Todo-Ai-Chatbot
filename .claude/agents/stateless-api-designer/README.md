# Stateless API Designer Subagent

## Overview
This subagent designs stateless HTTP APIs for cloud-native applications. It focuses on creating RESTful endpoints that support horizontal scaling, follow HTTP semantics, and maintain no server-side session state.

## Purpose
To provide complete API specifications for the Phase III Todo Chatbot backend, including:
- HTTP endpoint definitions
- Request/response schemas
- Authentication and authorization
- Error handling
- Rate limiting
- CORS configuration
- Stateless architecture validation

## What This Subagent Produces

The agent.md file documents:

### 1. Core API Endpoints
- **POST /api/{user_id}/chat** - Send message to chatbot
- **GET /api/{user_id}/conversations** - List user's conversations
- **GET /api/{user_id}/conversations/{id}/messages** - Get conversation messages
- **DELETE /api/{user_id}/conversations/{id}** - Delete conversation
- **GET /health** - Health check endpoint

### 2. Complete Endpoint Specifications
For each endpoint:
- HTTP method and URL path
- Request headers (authentication)
- Request body (JSON schema)
- Response body (JSON schema)
- All possible error responses (400, 401, 403, 404, 429, 500, 503)
- Rate limits
- Idempotency guarantees
- Example cURL commands

### 3. Authentication & Authorization
- JWT token structure and claims
- Token validation flow
- Authorization rules (user isolation)
- Error handling for auth failures

### 4. Error Response Format
- Consistent error structure across all endpoints
- Standard error types (ValidationError, Unauthorized, etc.)
- HTTP status code mapping
- Request ID for tracking

### 5. Rate Limiting Strategy
- Per-endpoint rate limits
- Rate limit headers (X-RateLimit-*)
- 429 Too Many Requests handling
- Retry-After guidance

### 6. Stateless Architecture Verification
- Checklist ensuring no server-side sessions
- JWT-based authentication
- Database as single source of truth
- Horizontal scaling support

### 7. Security Best Practices
- Input validation requirements
- Authentication verification
- Authorization checks
- XSS prevention
- Error message sanitization

## Key Design Principles

### Statelessness
- **No Server Memory:** All state in database or JWT
- **Independent Requests:** Each request contains full context
- **Horizontal Scaling:** Add servers without configuration changes
- **Restart-Safe:** Server restart doesn't affect users

### REST Semantics
- **GET:** Retrieve data (safe, idempotent, cacheable)
- **POST:** Create resources (non-idempotent)
- **DELETE:** Remove resources (idempotent)
- **Proper Status Codes:** 2xx success, 4xx client error, 5xx server error

### Security by Design
- **JWT Authentication:** Every endpoint (except /health)
- **User Isolation:** Path user_id must match JWT user_id
- **Input Validation:** All request bodies validated against schemas
- **Rate Limiting:** Prevent abuse and DoS attacks

### Developer Experience
- **Consistent Errors:** Same format across all endpoints
- **Clear Documentation:** Examples for every endpoint
- **Predictable Behavior:** HTTP semantics followed correctly
- **Request IDs:** Track requests through logs

## API Architecture Highlights

### Stateless Flow
```
Client Request (JWT + Body) → Any Server Instance →
JWT Validation → Database Query → Response
```

### Authentication
```
Authorization: Bearer eyJhbGc...
↓
Extract & Verify JWT
↓
user_id from claims
↓
Validate path user_id matches JWT user_id
```

### Error Handling
```
Error Occurs → Determine Type → Select Status Code →
Format Error Response → Log Details → Return to Client
```

### Rate Limiting
```
Request → Extract user_id from JWT →
Check rate limit counter → If exceeded: 429 →
If ok: Process request → Update counter
```

## Endpoint Summary

| Endpoint | Method | Purpose | Auth | Rate Limit |
|----------|--------|---------|------|------------|
| /api/{user_id}/chat | POST | Send message | Required | 100/hr, 20/min |
| /api/{user_id}/conversations | GET | List conversations | Required | 1000/hr |
| /api/{user_id}/conversations/{id}/messages | GET | Get messages | Required | 1000/hr |
| /api/{user_id}/conversations/{id} | DELETE | Delete conversation | Required | 100/hr |
| /health | GET | Health check | Not required | Unlimited |

## Related Specifications

This API design is based on:
- **Constitution**: `.specify/memory/constitution.md` - Stateless architecture principle
- **Chatbot Spec**: `specs/001-chatbot/spec.md` - Feature requirements
- **Database Schema**: `specs/004-chat-schema/spec.md` - Data model
- **Orchestrator**: `.claude/agents/agent-orchestrator/agent.md` - Backend processing

## Implementation Guidance

### For Backend Developers (FastAPI)
1. Read agent.md endpoint specifications
2. Implement each endpoint following the contract
3. Use Pydantic models for request/response validation
4. Implement JWT middleware for authentication
5. Add rate limiting middleware
6. Follow error response format exactly

### For Frontend Developers (OpenAI ChatKit)
1. Use documented endpoints for chat functionality
2. Include JWT in Authorization header
3. Handle all documented error responses
4. Respect rate limit headers
5. Implement retry logic for 429 responses

### For DevOps/Infrastructure
1. Configure CORS for allowed origins
2. Set up rate limiting at API gateway (optional)
3. Monitor /health endpoint
4. Ensure HTTPS in production
5. Configure load balancer without sticky sessions

## Testing Requirements

### Contract Tests
- Request schemas validated
- Response schemas validated
- All error scenarios tested
- HTTP status codes correct

### Security Tests
- JWT validation (missing, invalid, expired)
- User isolation (accessing other users' data)
- Rate limiting triggers correctly
- CORS headers set properly

### Performance Tests
- Response times meet targets
- Horizontal scaling works (multiple instances)
- No session affinity needed
- Rate limits don't block legitimate traffic

### Statelessness Tests
- Server restart doesn't break functionality
- Same request to different servers produces same result
- No shared memory required between instances

## Example Usage

### Send Chat Message
```bash
curl -X POST https://api.example.com/api/user123/chat \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 456,
    "message": "add task to buy groceries"
  }'
```

### List Conversations
```bash
curl -X GET "https://api.example.com/api/user123/conversations?limit=10&sort=updated_at&order=desc" \
  -H "Authorization: Bearer eyJhbGc..."
```

### Get Messages
```bash
curl -X GET https://api.example.com/api/user123/conversations/456/messages \
  -H "Authorization: Bearer eyJhbGc..."
```

### Health Check
```bash
curl -X GET https://api.example.com/health
```

## Common Questions

**Q: Why is user_id in the path instead of extracting it from JWT?**
A: Explicit user_id in path makes URLs RESTful and self-documenting. We validate it matches JWT for security.

**Q: Why separate endpoints for conversations and messages?**
A: Follows REST resource hierarchy. Conversations are resources, messages are sub-resources.

**Q: Why is /health endpoint public?**
A: Health checks need to work even if auth service is down. Used by monitoring/load balancers.

**Q: Why rate limit by user_id instead of IP?**
A: IP-based limiting doesn't work behind proxies/NAT. User-based is more accurate for authenticated APIs.

**Q: Why 204 No Content for DELETE?**
A: Standard REST practice. Successful deletion doesn't need response body.

## Success Criteria

The API is correctly implemented when:

1. **OpenAI ChatKit Integration Works:** Frontend can call all endpoints
2. **Stateless Verified:** Multiple backend instances work without sticky sessions
3. **Security Enforced:** Users can only access their own data
4. **Errors Handled:** All error scenarios return documented responses
5. **Rate Limits Work:** Abuse prevention without blocking legitimate users
6. **Performance Met:** Response times meet targets
7. **CORS Configured:** Cross-origin requests work properly

---

**Status**: Complete API specification. Ready for FastAPI implementation.
