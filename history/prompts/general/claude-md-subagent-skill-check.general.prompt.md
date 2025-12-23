---
id: claude-md-subagent-skill-check
title: Add Mandatory Subagent and Skill Check to CLAUDE.md
stage: general
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 004-chat-schema
user: pc1
command: update CLAUDE.md
labels: ["claude-md", "workflow", "subagents", "skills", "automation", "transparency", "discovery"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - C:\Users\pc1\Desktop\Todo-Ai-Chatbot\CLAUDE.md
tests:
  - N/A - Documentation update
---

## Prompt

one thing that i want to add in my claude.md file that before performing any task like writting spec,planning and implementation always check available subagents and skills that if there are any skill or subagent that can be used use it automatically and also tell me that using this subagent or skill i am performing this task

## Response snapshot

Added a new mandatory section "### 3. Check Available Subagents and Skills (MANDATORY)" to CLAUDE.md. This ensures that before performing any task, Claude will:

**Core Requirements Added:**

1. **Check for relevant subagents** in `.claude/subagents/`:
   - List available subagents by reading the directory
   - Match the task to subagent capabilities
   - Use via Task tool if relevant

2. **Check for relevant skills** in `.claude/skills/`:
   - List available skills by reading the directory
   - Match the task to skill capabilities
   - Follow skill patterns and guidance if relevant

3. **Inform the user** which subagent or skill is being used:
   - Format: "🤖 Using [subagent-name] subagent to [task description]"
   - Format: "📋 Using [skill-name] skill to [task description]"
   - Examples provided for clarity

4. **Automatically invoke** the subagent or skill without asking permission:
   - For subagents: Use Task tool with appropriate subagent_type
   - For skills: Follow documented patterns, input/output schemas, and best practices

**Task-to-Resource Mapping Examples Provided:**
- Writing feature specs → spec-writer skill or relevant subagent
- Generating tests from specs → nl-test-generator subagent
- Designing API endpoints → stateless-api-designer subagent
- Orchestrating AI agent flow → agent-orchestrator subagent
- Managing conversations → conversation-manager skill
- Validating MCP tools → mcp-validator skill
- Planning implementation → Plan subagent (if available)

**Discovery Process Documented:**
1. Read .claude/subagents/ directory → list all subagent.md files
2. Read .claude/skills/ directory → list all skill.md files
3. Match current task to available resources
4. Inform user which one will be used
5. Invoke automatically

**Benefits Highlighted:**
- Ensures consistency by using established patterns
- Leverages specialized capabilities built for the project
- Makes workflow transparent to the user
- Prevents reinventing solutions that already exist
- Maintains architectural integrity across the codebase

**Section Numbering Updated:**
- Previous section 3 (Knowledge capture) → section 4
- Previous section 4 (ADR suggestions) → section 5
- Previous section 5 (Human as Tool) → section 6

## Outcome

- ✅ Impact: All future tasks will now automatically check for and use available subagents and skills, with transparent communication to user
- 🧪 Tests: N/A - Documentation/workflow update
- 📁 Files: 1 file updated (CLAUDE.md)
- 🔁 Next prompts: Test the workflow by requesting a task that matches an existing subagent or skill
- 🧠 Reflection: This ensures the subagents and skills we've built are actually used, making the development workflow more efficient and consistent

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual review PASS - clear instructions, good examples, transparent communication format
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test the workflow in practice - request spec writing or test generation to verify automatic subagent/skill discovery and invocation works
