# Agent Workflow

Last updated: 2026-06-19

## Purpose

This document defines accepted tool lanes for AI Health Coach development.

The goal is to make coding sessions faster and safer without changing product runtime behavior.

## Operating model

The user remains project owner, command runner, final approver, merge owner, and snapshot owner.

Coding tools may help generate patches, inspect context, suggest tests, or prepare handoffs, but they do not own architecture decisions.

## Tool lanes

### ChatGPT

Primary lane:

- Architecture discussion
- TPM/milestone control
- QA review
- handoff generation
- implementation planning
- product reasoning
- patch generation when scoped

ChatGPT should preserve project memory, scope boundaries, validation expectations, and deterministic/backend-truth-first doctrine.

### User

Primary lane:

- project owner
- command runner
- final approver
- merge owner
- snapshot owner
- manual QA witness

The user decides when work is accepted and merged.

### Codex / OpenAI coding helpers

Accepted lane:

- optional scoped implementation worker
- small bounded tasks
- failing-test repair when supplied exact scope
- no architecture ownership
- no broad autonomous rewrites

Codex should receive a context pack with source-of-truth docs, branch, milestone, scope, non-goals, expected files, and validation commands.

Codex is not required for normal development.

### Aider-style patch helpers

Accepted lane:

- surgical patch helper
- failing-test fixes
- small file-scoped edits

Aider-style tools should not expand scope or redesign architecture.

### GitHub Copilot

Accepted lane:

- IDE autocomplete/helper
- local refactor suggestions
- small code snippets

Copilot is not an architecture owner, QA owner, or milestone owner.

### Dev Assistant

Accepted lane:

- local project cockpit
- repo state summary
- project-memory checks
- stale-doc checks
- prompt/context-pack generation
- validation guidance
- snapshot command helper
- Windows/Linux sync reminders
- deterministic-safe restart guidance

Dev Assistant must remain local/read-only unless a future tooling milestone explicitly approves write actions.

### Headroom

Future lane only:

- developer-workflow context compression spike
- optional context-pack compression experiment

Headroom is not runtime product logic and is not a provider prompt compression dependency in Supercharger v1.

### Claude

Out of scope.

Do not add:

- `CLAUDE.md`
- Claude Code commands
- Claude-specific workflow lanes
- Claude-specific prompt generators

## Context pack requirements

Generated implementation prompts should include:

- project and branch
- latest commit
- milestone
- source-of-truth docs to read
- scope
- strict non-goals
- expected files
- validation commands
- acceptance criteria
- artifact and snapshot rules
- provider/validator/fallback boundaries
- reminder that coding agents are scoped workers only

## Runtime safety reminder

Development tooling must not alter product runtime behavior.

Supercharger v1 does not change FastAPI, Streamlit product surfaces, provider defaults, validators, persistence, reports, nutrition, training, or catalog behavior.
