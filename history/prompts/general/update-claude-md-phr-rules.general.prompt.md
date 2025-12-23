---
id: update-claude-md-phr-rules
title: Update CLAUDE.md with PHR rules
stage: general
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5
feature: none
branch: 003-mcp-tools-spec
user: Your
command: general
labels: ["documentation", "phr", "claude-md", "configuration", "workflow"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - CLAUDE.md
  - history/prompts/mcp-tools-spec/mcp-tools-specification-creation.spec.prompt.md
tests:
  - none
---

## Prompt

i think you should add this in claude.md file then it will remember and will always maintain prompt hisory

always maintain prompt history and gernal prompts also in gernal prompt folder

remove numbeer from PHR

i am seeing it is still 003-mcp-tool spec at this location C:\Users\pc1\Desktop\Todo-Ai-Chatbot\history\prompts

dont number it just mcp-tools folder name is fine

## Response snapshot

Updated CLAUDE.md with comprehensive PHR rules emphasizing automatic creation without asking permission, proper routing (feature/general/constitution), and use of descriptive slugs instead of numeric prefixes. Renamed history/prompts/003-mcp-tools-spec to mcp-tools-spec and updated PHR ID to use descriptive slug format.

## Outcome

- ✅ Impact: CLAUDE.md now mandates automatic PHR creation for all interactions with clear routing rules and no-numbering policy, ensuring consistent prompt history maintenance
- 🧪 Tests: Validated PHR routing by renaming directory and updating file metadata
- 📁 Files: CLAUDE.md (updated 5 sections), history/prompts/mcp-tools-spec/ (renamed from 003-mcp-tools-spec)
- 🔁 Next prompts: Test PHR auto-creation on next interaction to verify rules are being followed
- 🧠 Reflection: Adding rules to CLAUDE.md ensures persistence across sessions - configuration as documentation is more reliable than in-memory instructions

## Evaluation notes (flywheel)

- Failure modes observed: None - successfully updated all references to use descriptive slugs and emphasized automatic PHR creation
- Graders run and results (PASS/FAIL): Manual validation - PASS (all CLAUDE.md sections updated consistently, directory renamed, PHR metadata corrected)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Monitor next few interactions to ensure PHRs are created automatically without prompting and routed correctly to general/ or feature-slug/ folders
