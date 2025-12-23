---
id: nl-test-generator-subagent-creation
title: Natural Language Test Generator subagent creation
stage: general
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 004-chat-schema
user: Your
command: general
labels: ["subagent", "testing", "test-generation", "quality-assurance", "given-when-then", "test-pyramid"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agents/nl-test-generator/agent.md
  - .claude/agents/nl-test-generator/README.md
tests:
  - none
---

## Prompt

lets build Natural Language Test Generator Subagent

## Response snapshot

Created comprehensive Natural Language Test Generator subagent following established pattern. Documented complete test specification generation approach including test pyramid strategy (70% unit, 20% integration, 10% E2E), Given-When-Then patterns, test data fixtures, mocking strategies, assertion patterns, and coverage requirements (80% minimum). Provided test naming conventions, test organization structure, and CI/CD integration guidance.

## Outcome

- ✅ Impact: Complete test generator subagent created at .claude/agents/nl-test-generator/ with full test specification methodology covering test case generation from acceptance scenarios, test pyramid distribution, mocking strategies, assertion patterns, and comprehensive coverage requirements
- 🧪 Tests: Testing strategy documented covering unit tests (70%), integration tests (20%), E2E tests (10%), with coverage targets (80% code coverage minimum, 100% scenario coverage)
- 📁 Files: .claude/agents/nl-test-generator/agent.md (created - 785+ lines), .claude/agents/nl-test-generator/README.md (created)
- 🔁 Next prompts: Use test generator to create test specifications from chatbot acceptance scenarios, or continue building additional subagents
- 🧠 Reflection: Successfully designed test generator as quality assurance tool - translates natural language specs into executable test documentation using Given-When-Then format, maintains test pyramid principles, and ensures comprehensive coverage across all test types while remaining technology-agnostic

## Evaluation notes (flywheel)

- Failure modes observed: None - subagent created following established pattern from agent-orchestrator and stateless-api-designer
- Graders run and results (PASS/FAIL): Manual validation - PASS (comprehensive test specification methodology, clear test pyramid strategy, complete example test case, realistic coverage requirements)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Generate actual test specifications from existing chatbot acceptance scenarios to validate test generator's output format and completeness
