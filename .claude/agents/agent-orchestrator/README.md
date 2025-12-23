# OpenAI Agent Orchestrator Subagent

## Overview
This subagent designs the architecture for the AI orchestrator that powers the Phase III Todo Chatbot. The orchestrator manages conversation flow, invokes MCP tools, and generates natural language responses.

## Purpose
To provide a complete architectural specification for the agent orchestrator component, including:
- Request-response workflow
- Tool integration patterns
- Context management
- Error handling
- Security and isolation
- Performance optimization

## How to Use This Subagent

### Invocation (Conceptual)
```bash
# If this were a callable agent
claude --agent agent-orchestrator "Design the complete orchestrator architecture for Phase III chatbot"
```

### Current Usage
Since this is a design specification:
1. Read `agent.md` to understand the orchestrator architecture
2. Use the documented patterns when implementing the backend
3. Follow the design principles for all agent-related code
4. Reference the architecture diagram for system understanding

## What This Subagent Produces

The agent.md file documents:

### 1. Request-Response Flow
Complete workflow from HTTP request to database persistence:
- JWT validation and user extraction
- Conversation history retrieval
- OpenAI agent processing
- MCP tool invocation
- Response generation
- State persistence

### 2. System Prompt Design
Guidelines for configuring the AI agent's behavior:
- Capabilities definition
- Behavioral rules
- Tool usage patterns
- Error handling instructions

### 3. Tool Integration
How the orchestrator works with MCP tools:
- Tool registration
- Parameter extraction from natural language
- Error handling
- Result processing

### 4. Context Management
Strategy for managing conversation history:
- Message retrieval limits
- Token window optimization
- Message formatting
- Truncation strategy

### 5. Error Handling
Comprehensive error scenarios:
- Tool execution errors
- AI service failures
- Database errors
- Validation errors
- Authentication errors

### 6. Security Specifications
User isolation and protection:
- Authentication flow
- Data isolation enforcement
- Input sanitization
- Rate limiting

### 7. Performance Targets
Response time SLAs and optimization:
- p50, p95, p99 latency targets
- Parallel processing strategies
- Connection pooling
- Timeout limits

### 8. Configuration
Environment variables and feature flags:
- OpenAI configuration
- Agent tuning parameters
- MCP server settings
- Database configuration

## Key Design Principles

### Statelessness
Every request is independent. No in-memory session state. All context retrieved from database.

### Conversational-First
Users interact in natural language. No commands, no syntax. AI interprets intent.

### MCP Tool Architecture
Orchestrator doesn't know database schema. All data operations via MCP tools.

### Security by Design
JWT validation, user isolation, input sanitization on every request.

## Architecture Highlights

### Core Flow
```
User Message → JWT Auth → Fetch Context → OpenAI Agent →
MCP Tools (if needed) → Generate Response → Store Messages → Return
```

### Stateless Design
- No conversation state in memory
- Database is source of truth
- Horizontal scaling supported
- Server restart-safe

### Tool Integration
- Agent decides which tools to call
- Orchestrator validates user_id
- Tools executed via MCP protocol
- Results used for response generation

## Related Specifications

This orchestrator design is based on:
- **Constitution**: `.specify/memory/constitution.md` - Core principles
- **Chatbot Spec**: `specs/001-chatbot/spec.md` - User requirements
- **MCP Tools Spec**: `specs/003-mcp-tools-spec/spec.md` - Tool contracts
- **Database Schema**: `specs/004-chat-schema/spec.md` - Data model

## Implementation Guidance

### For Backend Developers
1. Read `agent.md` sections in order
2. Start with Request-Response Flow
3. Implement each step with tests
4. Follow security specifications exactly
5. Meet performance targets

### For Frontend Developers
- Understand the HTTP API contract
- Know what response format to expect
- Handle error scenarios gracefully

### For System Architects
- Review architecture diagram
- Validate against constitution principles
- Ensure scalability considerations are met

## Testing Requirements

The orchestrator must be tested for:
- **Unit Tests**: Individual components (message formatting, error handling)
- **Integration Tests**: Full flow with mock MCP tools
- **E2E Tests**: Real conversations with real database and tools
- **Error Scenarios**: Every documented error path

## Success Criteria

The orchestrator is correctly implemented when:
1. Users can have natural conversations without commands
2. All task operations work via conversational input
3. User data is isolated (zero cross-user access)
4. Response times meet p95 < 3 seconds
5. Errors are handled gracefully with user-friendly messages
6. Server restarts don't lose conversation context

## Questions or Clarifications?

If the agent.md specification is unclear:
1. Check related specifications (constitution, chatbot spec, MCP tools spec)
2. Review the architecture diagram
3. Look at example tool call sequences
4. Consult the testing strategy section

---

**Status**: Design specification complete. Ready for implementation planning and coding.
