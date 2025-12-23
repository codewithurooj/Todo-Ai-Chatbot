---
id: mcp-tools-spec
title: MCP tools specification creation
stage: spec
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5
feature: mcp-tools-spec
branch: 003-mcp-tools-spec
user: Your
command: /sp.specify
labels: ["mcp-tools", "specification", "api-contract", "task-management", "ai-agent"]
links:
  spec: specs/003-mcp-tools-spec/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-mcp-tools-spec/spec.md
  - specs/003-mcp-tools-spec/checklists/requirements.md
tests:
  - none
---

## Prompt

using spec-writer skill that is placed in my claude folder inside that there is skill folder and inside that there is a skill spec-writer using that skill write spec for the following Read speckitplus.constitution and all existing Phase III specs.

Create an MCP tools specification at:
specs/api/mcp-tools.md

Scope:
- Tools the AI agent is allowed to use to manage todos

The spec MUST include:
- Tool name
- Purpose
- Input parameters
- Output format
- Error cases

Required tools:
- add_task
- list_tasks
- update_task
- complete_task
- delete_task

Rules:
- Tools must be stateless
- Tools must require user_id
- This is a contract, not code
- Do NOT describe database internals

Only generate the MCP tools spec.

## Response snapshot

Created comprehensive MCP tools specification defining 5 stateless tools (add_task, list_tasks, complete_task, update_task, delete_task) with complete JSON schemas, input/output formats, error cases, 50 functional requirements, and quality validation checklist. Specification follows technology-agnostic contract approach per constitution principles.

## Outcome

- ✅ Impact: Complete, validated MCP tools specification created at specs/003-mcp-tools-spec/spec.md with 5 tool contracts, 50 functional requirements, comprehensive schemas, and quality checklist
- 🧪 Tests: Quality validation checklist completed - all items passed (content quality, requirement completeness, feature readiness)
- 📁 Files: specs/003-mcp-tools-spec/spec.md (created), specs/003-mcp-tools-spec/checklists/requirements.md (created)
- 🔁 Next prompts: Run `/sp.plan` to design implementation architecture, or `/sp.clarify` if clarifications needed (none currently)
- 🧠 Reflection: Successfully created technology-agnostic tool contracts following constitution's MCP architecture principle - specs describe WHAT tools do without HOW they're implemented

## Evaluation notes (flywheel)

- Failure modes observed: Initial script created spec in wrong directory (C:\Users\pc1\specs instead of project location), required manual correction to proper location and renumbering from 001 to 003
- Graders run and results (PASS/FAIL): Specification quality checklist - PASS (all 14 validation criteria met)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Ensure create-new-feature.sh uses absolute project path from git repo root to prevent directory mismatches
