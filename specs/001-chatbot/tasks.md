---
description: "Implementation tasks for AI-Powered Todo Chatbot"
---

# Tasks: AI-Powered Todo Chatbot

**Input**: Design documents from `/specs/001-chatbot/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/agent-orchestrator.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in feature specification - test tasks omitted per template guidance

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Exact file paths included in descriptions

## Path Conventions

Web application structure (per plan.md):
- Backend: `backend/app/` for application code
- Frontend: `frontend/` for Next.js/ChatKit code
- Tests: `backend/tests/` for pytest tests
- Migrations: `backend/migrations/` for Alembic migrations

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend project structure: backend/app/{__init__.py,main.py,config.py,database.py}
- [X] T002 Create backend subdirectories: backend/app/{models,mcp,agent,routes,middleware}/
- [X] T003 [P] Initialize Python project with UV: backend/pyproject.toml with FastAPI, SQLModel, OpenAI SDK, MCP SDK dependencies
- [X] T004 [P] Create backend/.env.example with DATABASE_URL, OPENAI_API_KEY, BETTER_AUTH_SECRET, MCP_SERVER_URL placeholders
- [X] T005 [P] Create frontend project structure with Next.js and OpenAI ChatKit: frontend/{app,components,lib}/
- [X] T006 [P] Initialize frontend with npm: frontend/package.json with better-auth, next, react dependencies
- [X] T007 [P] Create frontend/.env.local.example with NEXT_PUBLIC_API_URL, BETTER_AUTH_SECRET placeholders
- [X] T008 [P] Configure linting: backend/.flake8, frontend/.eslintrc.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create User model in backend/app/models/user.py per data-model.md schema
- [ ] T010 [P] Create Task model in backend/app/models/task.py per data-model.md schema
- [ ] T011 [P] Create Conversation model in backend/app/models/conversation.py per data-model.md schema
- [ ] T012 [P] Create Message model in backend/app/models/message.py per data-model.md schema
- [ ] T013 Setup database connection in backend/app/database.py with SQLModel engine, session management, connection pooling
- [ ] T014 Initialize Alembic in backend/migrations/ with alembic.ini configuration
- [ ] T015 Generate initial database migration in backend/migrations/versions/001_initial_schema.py for all 4 tables
- [ ] T016 [P] Implement JWT validation middleware in backend/app/middleware/auth.py extracting user_id from Bearer token
- [ ] T017 [P] Implement global error handler in backend/app/middleware/error_handler.py with consistent error response format
- [ ] T018 [P] Create environment config loader in backend/app/config.py loading from .env file
- [ ] T019 Initialize MCP server in backend/app/mcp/server.py with Official MCP SDK
- [ ] T020 [P] Create MCP tool registration helper in backend/app/mcp/tools/__init__.py
- [ ] T021 Initialize OpenAI agent orchestrator in backend/app/agent/orchestrator.py with Agents SDK
- [ ] T022 [P] Create system prompt in backend/app/agent/system_prompt.py per contracts/agent-orchestrator.md template
- [ ] T023 [P] Create conversation manager in backend/app/agent/conversation_manager.py for history retrieval/storage
- [ ] T024 Create health check endpoint in backend/app/routes/health.py with database/OpenAI/MCP status checks
- [ ] T025 [P] Setup FastAPI app in backend/app/main.py with CORS, middleware registration, route inclusion
- [ ] T026 [P] Create Better Auth configuration in frontend/lib/auth.ts with JWT plugin
- [ ] T027 [P] Create API client helper in frontend/lib/api.ts for backend chat endpoint calls

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create Tasks via Natural Language (Priority: P1) 🎯 MVP

**Goal**: Users can create todo tasks by expressing intentions in natural conversational language

**Independent Test**: User sends "I need to buy groceries" and system creates task "Buy groceries" with confirmation message

### Implementation for User Story 1

- [ ] T028 [US1] Implement add_task MCP tool in backend/app/mcp/tools/add_task.py per contracts/mcp-tools.md spec
- [ ] T029 [US1] Register add_task tool with MCP server in backend/app/mcp/server.py
- [ ] T030 [US1] Update system prompt in backend/app/agent/system_prompt.py with create task intent patterns and examples
- [ ] T031 [US1] Implement POST /api/{user_id}/chat endpoint in backend/app/routes/chat.py with conversation creation, agent invocation, message storage
- [ ] T032 [US1] Integrate add_task tool with agent orchestrator in backend/app/agent/orchestrator.py
- [ ] T033 [US1] Create ChatInterface component in frontend/components/ChatInterface.tsx using OpenAI ChatKit
- [ ] T034 [US1] Create chat page in frontend/app/page.tsx with authentication and ChatInterface integration
- [ ] T035 [US1] Implement API route proxy in frontend/app/api/chat/route.ts forwarding to backend

**Checkpoint**: User Story 1 complete - users can create tasks via natural language

---

## Phase 4: User Story 2 - View and List Tasks Conversationally (Priority: P1)

**Goal**: Users can view their todo list by asking natural questions like "what's on my list?"

**Independent Test**: User asks "show my tasks" and receives formatted list of all pending tasks

### Implementation for User Story 2

- [ ] T036 [US2] Implement list_tasks MCP tool in backend/app/mcp/tools/list_tasks.py per contracts/mcp-tools.md spec with filter parameter
- [ ] T037 [US2] Register list_tasks tool with MCP server in backend/app/mcp/server.py
- [ ] T038 [US2] Update system prompt in backend/app/agent/system_prompt.py with list tasks intent patterns ("show my list", "what do I need to do?")
- [ ] T039 [US2] Integrate list_tasks tool with agent orchestrator in backend/app/agent/orchestrator.py
- [ ] T040 [US2] Update ChatInterface component in frontend/components/ChatInterface.tsx to render task lists with formatting

**Checkpoint**: User Stories 1 AND 2 complete - users can create and view tasks conversationally

---

## Phase 5: User Story 3 - Mark Tasks Complete Through Conversation (Priority: P1)

**Goal**: Users can mark tasks as done using natural language like "I finished buying groceries"

**Independent Test**: User says "done with groceries" and system marks matching task complete with confirmation

### Implementation for User Story 3

- [ ] T041 [US3] Implement complete_task MCP tool in backend/app/mcp/tools/complete_task.py per contracts/mcp-tools.md spec
- [ ] T042 [US3] Register complete_task tool with MCP server in backend/app/mcp/server.py
- [ ] T043 [US3] Update system prompt in backend/app/agent/system_prompt.py with complete task intent patterns ("finished X", "done with X", "mark X as done")
- [ ] T044 [US3] Implement task matching logic in backend/app/agent/orchestrator.py for ambiguous references (list tasks first, find match)
- [ ] T045 [US3] Add ambiguity handling to system prompt: clarifying questions when multiple tasks match

**Checkpoint**: User Stories 1, 2, AND 3 complete - core P1 functionality delivered (MVP ready!)

---

## Phase 6: User Story 4 - Delete Tasks Conversationally (Priority: P2)

**Goal**: Users can remove unwanted tasks by expressing deletion intent naturally

**Independent Test**: User says "delete the groceries task" and system removes task with confirmation

### Implementation for User Story 4

- [ ] T046 [US4] Implement delete_task MCP tool in backend/app/mcp/tools/delete_task.py per contracts/mcp-tools.md spec
- [ ] T047 [US4] Register delete_task tool with MCP server in backend/app/mcp/server.py
- [ ] T048 [US4] Update system prompt in backend/app/agent/system_prompt.py with delete task intent patterns ("delete X", "remove X", "cancel X")
- [ ] T049 [US4] Integrate delete_task tool with agent orchestrator in backend/app/agent/orchestrator.py
- [ ] T050 [US4] Add delete confirmation patterns to system prompt for user-friendly acknowledgments

**Checkpoint**: User Stories 1-4 complete - users can create, view, complete, and delete tasks

---

## Phase 7: User Story 5 - Update Tasks Through Natural Edits (Priority: P2)

**Goal**: Users can modify task details by describing changes conversationally

**Independent Test**: User says "change groceries to buy groceries and milk" and system updates task title

### Implementation for User Story 5

- [ ] T051 [US5] Implement update_task MCP tool in backend/app/mcp/tools/update_task.py per contracts/mcp-tools.md spec
- [ ] T052 [US5] Register update_task tool with MCP server in backend/app/mcp/server.py
- [ ] T053 [US5] Update system prompt in backend/app/agent/system_prompt.py with update task intent patterns ("change X to Y", "rename X", "update X")
- [ ] T054 [US5] Integrate update_task tool with agent orchestrator in backend/app/agent/orchestrator.py
- [ ] T055 [US5] Add update confirmation patterns to system prompt with old and new values

**Checkpoint**: User Stories 1-5 complete - full CRUD operations available via natural language

---

## Phase 8: User Story 6 - Multi-Turn Contextual Conversations (Priority: P3)

**Goal**: Users can engage in back-and-forth conversations with context from previous messages

**Independent Test**: User creates task, then says "actually, delete that one" and system understands "that one" refers to just-created task

### Implementation for User Story 6

- [ ] T056 [US6] Enhance conversation history retrieval in backend/app/agent/conversation_manager.py to fetch last 20 messages per contracts/agent-orchestrator.md
- [ ] T057 [US6] Implement context window management in backend/app/agent/conversation_manager.py with 4000-token limit and truncation
- [ ] T058 [US6] Update system prompt in backend/app/agent/system_prompt.py with contextual reference handling ("that one", "the first task", "it")
- [ ] T059 [US6] Add conversation context formatting in backend/app/agent/orchestrator.py for OpenAI API messages array
- [ ] T060 [US6] Implement task persistence across sessions in GET /api/{user_id}/conversations endpoint in backend/app/routes/conversations.py
- [ ] T061 [US6] Create GET /api/{user_id}/conversations/{id}/messages endpoint in backend/app/routes/conversations.py
- [ ] T062 [US6] Add conversation history UI in frontend/components/ChatInterface.tsx showing previous messages

**Checkpoint**: All user stories complete - full conversational AI task management experience delivered

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T063 [P] Add input validation for message length (1-10000 chars) in backend/app/routes/chat.py
- [ ] T064 [P] Add input sanitization (HTML escape, null byte check) in backend/app/middleware/error_handler.py
- [ ] T065 [P] Implement rate limiting in backend/app/middleware/auth.py: 100 requests/hour, 20/minute per user
- [ ] T066 [P] Add request logging in backend/app/main.py with request_id for traceability
- [ ] T067 [P] Optimize database queries in backend/app/mcp/tools/ with proper indexes verification
- [ ] T068 [P] Add error response formatting in backend/app/middleware/error_handler.py per contracts/agent-orchestrator.md
- [ ] T069 [P] Create DELETE /api/{user_id}/conversations/{id} endpoint in backend/app/routes/conversations.py
- [ ] T070 [P] Add CORS configuration in backend/app/main.py for production frontend domain
- [ ] T071 [P] Create backend/README.md with setup instructions per quickstart.md
- [ ] T072 [P] Create frontend/README.md with setup instructions per quickstart.md
- [ ] T073 [P] Add production environment variable validation in backend/app/config.py
- [ ] T074 [P] Implement graceful error messages in system prompt for OpenAI API failures
- [ ] T075 Run quickstart.md validation: verify all setup steps work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-8)**: All depend on Foundational (Phase 2) completion
  - User stories can proceed in parallel (if team capacity allows)
  - Or sequentially in priority order: US1 → US2 → US3 → US4 → US5 → US6
- **Polish (Phase 9)**: Depends on desired user stories being complete (minimum: US1-US3 for MVP)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - **No dependencies** on other stories
- **User Story 2 (P1)**: Can start after Foundational - Uses list_tasks (independent of US1 add_task)
- **User Story 3 (P1)**: Can start after Foundational - May need list_tasks for task matching, but independently testable
- **User Story 4 (P2)**: Can start after Foundational - Independent implementation
- **User Story 5 (P2)**: Can start after Foundational - Independent implementation
- **User Story 6 (P3)**: Can start after Foundational - Uses existing conversation infrastructure

### Within Each User Story

- MCP tool implementation before agent integration
- System prompt updates before orchestrator integration
- Backend implementation before frontend integration
- Each story independently complete before moving to next priority

### Parallel Opportunities

- **Setup Phase**: All tasks marked [P] can run in parallel (T003-T008)
- **Foundational Phase**: Models (T009-T012), middleware (T016-T017), agent components (T022-T023), frontend setup (T026-T027) can run in parallel
- **User Stories**: Once Foundational complete, all user stories can start in parallel (if team capacity)
- **Polish Phase**: All tasks marked [P] can run in parallel (T063-T074)

---

## Parallel Example: User Story 1

```bash
# Sequential dependencies within US1:
# 1. First: Implement MCP tool
Task T028: "Implement add_task MCP tool in backend/app/mcp/tools/add_task.py"
Task T029: "Register add_task tool with MCP server"

# 2. Then: Update agent (depends on tool existing)
Task T030: "Update system prompt with create task intent"
Task T031: "Implement POST /api/{user_id}/chat endpoint"
Task T032: "Integrate add_task tool with agent orchestrator"

# 3. Finally: Frontend (depends on backend endpoint)
Task T033: "Create ChatInterface component"
Task T034: "Create chat page"
Task T035: "Implement API route proxy"
```

---

## Parallel Example: Multiple User Stories

```bash
# After Foundational Phase (T009-T027) completes, launch in parallel:

# Team Member A: User Story 1 (MVP core)
Tasks T028-T035: Create tasks functionality

# Team Member B: User Story 2 (MVP core)
Tasks T036-T040: List tasks functionality

# Team Member C: User Story 3 (MVP core)
Tasks T041-T045: Complete tasks functionality

# Each story is independently testable and deployable
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only)

1. **Complete Phase 1**: Setup (T001-T008) - ~2-3 hours
2. **Complete Phase 2**: Foundational (T009-T027) **CRITICAL** - ~1-2 days
3. **Complete Phase 3**: User Story 1 (T028-T035) - ~1 day
4. **Complete Phase 4**: User Story 2 (T036-T040) - ~4-6 hours
5. **Complete Phase 5**: User Story 3 (T041-T045) - ~4-6 hours
6. **STOP and VALIDATE**: Test all P1 stories independently
7. **Complete Phase 9**: Essential polish (T063-T068, T071-T075) - ~6-8 hours
8. **Deploy/Demo**: MVP ready with core P1 functionality

**MVP Scope**: 52 tasks (T001-T045 + essential polish)
**Expected Timeline**: 4-6 days for single developer, 2-3 days with 3 parallel developers

### Incremental Delivery

1. **Foundation**: Setup + Foundational → Infrastructure ready (T001-T027)
2. **MVP Release**: Add US1, US2, US3 → Test independently → Deploy (core P1 value)
3. **Enhancement 1**: Add US4 (Delete) → Test independently → Deploy
4. **Enhancement 2**: Add US5 (Update) → Test independently → Deploy
5. **Enhancement 3**: Add US6 (Context) → Test independently → Deploy
6. **Polish Release**: Complete Phase 9 → Production-ready

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers after Foundational phase:

1. **All**: Complete Setup + Foundational together (T001-T027)
2. **Parallel Development**:
   - **Developer A**: User Story 1 (T028-T035)
   - **Developer B**: User Story 2 (T036-T040)
   - **Developer C**: User Story 3 (T041-T045)
3. **Integration**: Verify all 3 stories work together
4. **Continue Parallel**:
   - **Developer A**: User Story 4 (T046-T050)
   - **Developer B**: User Story 5 (T051-T055)
   - **Developer C**: Polish tasks (T063-T075)

---

## Task Metrics

- **Total Tasks**: 75
- **Setup Phase**: 8 tasks
- **Foundational Phase**: 19 tasks (blocking)
- **User Story 1 (P1)**: 8 tasks 🎯 MVP
- **User Story 2 (P1)**: 5 tasks 🎯 MVP
- **User Story 3 (P1)**: 5 tasks 🎯 MVP
- **User Story 4 (P2)**: 5 tasks
- **User Story 5 (P2)**: 5 tasks
- **User Story 6 (P3)**: 7 tasks
- **Polish Phase**: 13 tasks

**Parallel Opportunities**: 28 tasks marked [P] can run in parallel
**Independent Stories**: All 6 user stories can be developed independently after Foundational phase

---

## Notes

- **[P] marker**: Tasks with different files and no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent delivery
- **MVP scope**: Focus on Phases 1-5 (T001-T045) + essential polish for production-ready core functionality
- **Incremental delivery**: Each user story adds value independently - stop at any checkpoint to validate
- **Constitution compliance**: All tasks align with 7 Phase 3 principles (stateless, conversational-first, MCP tools, etc.)
- **No test tasks**: Feature spec doesn't explicitly request TDD approach - tests omitted per template guidance
- **Commit strategy**: Commit after each task or logical group completion
- **Validation**: Stop at each checkpoint to test story independently before proceeding

---

**Format Validation**: ✅ All tasks follow strict checklist format with checkbox, ID, optional [P]/[Story] markers, and file paths
