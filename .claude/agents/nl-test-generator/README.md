# Natural Language Test Generator Subagent

## Overview
This subagent translates natural language specifications into comprehensive, executable test case documentation. It understands Given-When-Then patterns, test pyramid concepts, and quality assurance principles.

## Purpose
To generate complete test specifications from user stories and acceptance scenarios, enabling test engineers to write executable tests. This subagent produces **test documentation**, not code - defining what to test, how to test it, and what success looks like.

## What This Subagent Produces

The agent.md file documents:

### 1. Test Case Generation from Acceptance Scenarios
For each Given-When-Then scenario:
- Test case name following naming conventions
- Test type classification (Unit, Integration, E2E)
- Prerequisites and setup requirements
- Detailed test steps
- Expected results and assertions
- Test data specifications
- Cleanup procedures

### 2. Test Pyramid Strategy
- **Unit Tests (70%)** - Individual functions/methods
- **Integration Tests (20%)** - Component interactions
- **E2E Tests (10%)** - Complete user workflows
- Rationale for test level placement

### 3. Test Data Specifications
- Valid data for happy path scenarios
- Invalid data for error/edge cases
- Boundary values (min/max limits)
- Edge cases (null, empty, special characters)
- Realistic user scenarios

### 4. Mocking Strategy
Documentation for what should be mocked:
- External services (APIs, databases)
- MCP tools and responses
- Authentication (JWT tokens)
- Time/dates for consistency

### 5. Assertion Patterns
Specifications for what to verify:
- Response validation (status codes, structure)
- Data validation (fields, types, formats)
- State changes (database records)
- Error messages and types
- Side effects (tool calls, stored messages)

### 6. Coverage Requirements
- Code coverage targets (80% minimum)
- Scenario coverage (100% of acceptance scenarios)
- Error path coverage (all error cases)
- Edge case coverage (boundary conditions)

## Key Design Principles

### Test Pyramid Focus
- **70% Unit Tests:** Fast, isolated, focused on individual components
- **20% Integration Tests:** Medium speed, test component interactions
- **10% E2E Tests:** Slow, test complete user workflows
- **Rationale:** Faster feedback, easier debugging, better maintainability

### Given-When-Then Pattern
- **Given:** Initial conditions and prerequisites
- **When:** Action taken by user/system
- **Then:** Expected outcomes and assertions
- **Benefits:** Clear, business-readable, unambiguous test scenarios

### Technology-Agnostic Documentation
- **No Code:** Test specifications, not implementation
- **Framework Neutral:** Can be implemented in any testing framework
- **Portable:** Test logic remains valid across rewrites
- **Maintainable:** Specs update when requirements change, not when code refactors

### Comprehensive Coverage
- **Happy Paths:** All acceptance scenarios tested
- **Error Cases:** All documented error scenarios tested
- **Edge Cases:** Boundary conditions and special inputs
- **Security:** Authentication, authorization, input validation

## Test Output Template

### Test Plan Structure
```markdown
## Test Plan: {Feature Name}

### Overview
Brief description of what's being tested and why.

### Test Strategy
- Test Pyramid Distribution
- Coverage Targets

### Unit Tests
- Test suites organized by component
- Individual test specifications with Given-When-Then
- Mocking strategies
- Assertions

### Integration Tests
- Component interaction tests
- Database setup/cleanup
- Multi-component workflows

### E2E Tests
- Complete user journeys
- End-to-end workflows
- Real-world scenarios

### Error Scenario Tests
- All documented error cases
- Error response validation

### Edge Case Tests
- Boundary conditions
- Special inputs
- Test data matrices

### Test Data Fixtures
- User fixtures
- Conversation fixtures
- Task fixtures

### Coverage Requirements
- Code coverage targets
- Scenario coverage requirements
```

## Test Types Explained

### Unit Tests
**Purpose:** Test individual functions in isolation

**Characteristics:**
- Fast (< 1 second per test)
- No external dependencies
- Mock all collaborators
- Focus on single function behavior

**Example:**
```
Test: Validate JWT with expired token raises Unauthorized
Given: JWT token with exp claim in the past
When: validate_jwt() is called
Then: Raises UnauthorizedException
```

### Integration Tests
**Purpose:** Test component interactions

**Characteristics:**
- Medium speed (< 5 seconds per test)
- Real database/MCP connections
- Test multiple components together
- Verify data flows correctly

**Example:**
```
Test: Chat endpoint stores messages in database
Given: User has valid JWT, database is empty
When: POST /api/user123/chat with message
Then: Conversation and messages exist in database
```

### E2E Tests
**Purpose:** Test complete user workflows

**Characteristics:**
- Slow (5-30 seconds per test)
- Full stack testing
- Real HTTP requests
- Verify entire user journey

**Example:**
```
Test: User creates task, lists tasks, completes task
Given: New user with valid JWT
When: User creates task via chat, lists tasks, marks complete
Then: Task appears in list, status updates correctly
```

## Test Naming Conventions

### Unit Tests
**Format:** `test_{function_name}_{scenario}_{expected_result}`

**Examples:**
- `test_validate_jwt_with_valid_token_returns_user_id`
- `test_format_messages_with_empty_list_returns_empty_array`

### Integration Tests
**Format:** `test_{component_a}_and_{component_b}_{scenario}`

**Examples:**
- `test_orchestrator_and_mcp_server_create_task_successfully`
- `test_api_and_database_store_conversation_correctly`

### E2E Tests
**Format:** `test_{user_story_summary}`

**Examples:**
- `test_user_can_create_task_via_chat`
- `test_user_cannot_access_other_users_conversations`

## Mocking Strategy

### What to Mock (in unit tests)
- External APIs (OpenAI, Better Auth)
- Database connections
- MCP tool calls
- Time/date functions

### What NOT to Mock (in integration tests)
- Database (use test database)
- MCP server (use test instance)
- Internal components being tested

### What NEVER to Mock (in E2E tests)
- Complete stack should be real
- Only mock external paid services if necessary

## Coverage Requirements

### Code Coverage Targets
- **Overall:** 80% minimum
- **Critical Paths:** 100% (auth, user isolation, persistence)
- **Error Handling:** 90% (all error paths)
- **Utility Functions:** 70%

### Scenario Coverage
- **All Acceptance Scenarios:** 100% coverage
- **All Error Cases:** 100% coverage
- **All Edge Cases:** 80% coverage

### Coverage Reporting
```bash
# Conceptual commands
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing
```

## Test Data Fixtures

### User Fixtures
```json
{
  "test_user_1": {
    "user_id": "test_123",
    "email": "test@example.com",
    "jwt_token": "eyJhbGc..."
  }
}
```

### Conversation Fixtures
```json
{
  "empty_conversation": {
    "id": 1,
    "user_id": "test_123",
    "message_count": 0
  }
}
```

### Task Fixtures
```json
{
  "simple_task": {
    "task_id": 1,
    "title": "Buy groceries",
    "completed": false
  }
}
```

## Related Specifications

This test generator uses specifications from:
- **Chatbot Spec**: `specs/001-chatbot/spec.md` - Acceptance scenarios
- **MCP Tools Spec**: `specs/003-mcp-tools-spec/spec.md` - Tool contracts
- **Database Schema**: `specs/004-chat-schema/spec.md` - Data model
- **API Spec**: `.claude/agents/stateless-api-designer/agent.md` - HTTP endpoints
- **Orchestrator**: `.claude/agents/agent-orchestrator/agent.md` - Component integration

## Implementation Guidance

### For Test Engineers (Python/pytest)
1. Read agent.md test specifications
2. Implement each test following the Given-When-Then pattern
3. Use pytest fixtures for test data
4. Use pytest-mock for mocking external dependencies
5. Follow assertion patterns exactly as documented
6. Maintain test pyramid distribution (70/20/10)

### For Backend Developers
1. Write code to pass unit tests first
2. Ensure integration tests pass
3. Verify E2E tests pass before deployment
4. Maintain 80% code coverage minimum
5. Add regression tests for bugs

### For QA Engineers
1. Use test specifications for manual testing
2. Verify automated tests cover all scenarios
3. Add additional edge cases if discovered
4. Update test specs when requirements change

## Testing Best Practices

### Test Organization
```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_validation.py
│   └── test_message_formatting.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_orchestrator_mcp.py
│   └── test_database_operations.py
├── e2e/
│   ├── test_user_workflows.py
│   └── test_error_scenarios.py
├── fixtures/
│   ├── users.json
│   ├── conversations.json
│   └── tasks.json
└── conftest.py
```

### Test Execution Strategy
1. **Unit Tests** - Run on every commit (< 30 seconds)
2. **Integration Tests** - Run before merge (< 2 minutes)
3. **E2E Tests** - Run before deployment (< 5 minutes)

### CI/CD Integration
```yaml
# Conceptual pipeline
stages:
  - unit-tests      # Fast feedback
  - integration     # Verify components work together
  - e2e            # Verify complete workflows
  - coverage-check # Enforce minimum coverage
```

## Example: Complete Test Specification

### Feature: User Creates Task via Chat

**User Story:**
> Given a user starts a new conversation, When they say "I need to buy groceries", Then the system creates a task titled "Buy groceries" and confirms with a natural response.

**E2E Test:**
```markdown
Test: test_user_creates_first_task_in_new_conversation

Given:
- User has valid JWT token
- User has no existing conversations

When:
- User sends POST /api/test_e2e_001/chat
- Message: "I need to buy groceries"

Then:
- Response status: 200
- Conversation created in database
- 2 messages stored (user + assistant)
- Task created via MCP tool with title "Buy groceries"
- Response contains natural confirmation
```

## Common Questions

**Q: Why separate unit, integration, and E2E tests?**
A: Test pyramid provides faster feedback (unit tests run in seconds), easier debugging (unit tests isolate failures), and confidence (E2E tests verify complete workflows).

**Q: Why use Given-When-Then format?**
A: Makes tests business-readable, forces clarity on preconditions and expected outcomes, aligns with acceptance scenarios from specs.

**Q: Why 80% code coverage minimum?**
A: Balances comprehensive testing with diminishing returns. Critical paths require 100%, utilities can be lower.

**Q: Why mock external services in unit tests?**
A: Keeps tests fast, deterministic, and independent of external service availability or cost.

**Q: How do we handle flaky tests?**
A: Identify root cause (timing, state, randomness), fix properly, never ignore or disable without investigation.

## Success Criteria

The test specification is complete when:

1. **All Scenarios Covered:** Every Given-When-Then has a test
2. **Executable:** Test engineers can write code directly from specs
3. **Comprehensive:** Happy paths, errors, and edge cases included
4. **Maintainable:** Clear naming, organization, and documentation
5. **Realistic:** Test data represents actual user scenarios
6. **Automated:** Can run in CI/CD pipeline
7. **Fast:** Unit tests < 1 second, integration < 5 seconds per test

## Test Implementation Checklist

Before considering test specification complete:

- [ ] All acceptance scenarios have corresponding tests
- [ ] Test pyramid distribution is appropriate (70/20/10)
- [ ] All error cases from spec are tested
- [ ] Edge cases identified and tested
- [ ] Test data fixtures are defined
- [ ] Mocking strategy is documented
- [ ] Assertion patterns are clear
- [ ] Coverage targets are specified
- [ ] Test naming follows conventions
- [ ] Setup and cleanup steps are defined
- [ ] Test execution order is specified
- [ ] CI/CD integration is documented

---

**Status**: Complete test generation subagent. Ready to generate test specifications from acceptance scenarios.
