# Health & Fitness Platform Repository Instructions

## Product Boundaries

- Build a local-first health and fitness platform that is data-first, deterministic-first, and validation-first.
- Backend owns facts, calculations, constraints, validation, persistence, and fallback. The user approves consequential actions.
- Optional generative or provider systems may propose or explain backend-approved options, but they must never silently control health decisions.
- Preserve source and decision provenance. Do not replace validated data with unexplained generated output.
- Reuse existing services, contracts, models, and helpers before creating new implementations.
- Keep UI compact, practical, and focused on persisted backend state.
- Do not add provider defaults, RAG, embeddings, vector search, runtime agent orchestration, or health recommendations unless an authorized milestone explicitly scopes them.
- Deterministic fallback remains the default unless an authorized milestone explicitly changes that boundary.
- Do not add `CLAUDE.md` or parallel assistant-specific workflow files.

## Before Editing

1. Inspect the current branch, latest commit, `git status --short --untracked-files=all`, and relevant diffs.
2. Read `docs/project_memory/current_state.md`, the active milestone file, and any architecture contracts the work affects.
3. Compare the requested scope, non-goals, files, and validation commands with repository truth.
4. Preserve all existing uncommitted work. Do not reset, restore, discard, or destructively clean without explicit instruction.

Stop and report conflicts when the branch, base, working tree, or project memory does not match the handoff.

## Implementation Rules

- Modify only files required by the approved milestone. Leave unrelated refactors and formatting alone.
- Prefer narrow patches and existing ownership boundaries.
- Never mutate or commit the real `fitness_ai.db` during automated work.
- Use temporary databases or copies for tests and browser smoke. Remove temporary scripts, databases, logs, and reports before completion.
- Do not add dependencies, routes, schemas, persistence, or parallel workflow systems unless explicitly authorized.
- Do not stage, commit, push, merge, or create snapshots unless the user explicitly authorizes that action.

## Project memory update requirement

- Update project memory in the same branch for meaningful behavior, architecture, workflow, or accepted-status changes.
- Follow `docs/project_memory/developer_delivery_workflow_contract.md` and `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md` for delivery work.

## Validation

- Use targeted pytest slices by default; select commands from `docs/project_memory/validation_matrix.md` and expand them when milestone risk requires it.
- Run lint and build checks for touched areas.
- UI-impacting work requires production-mode browser smoke after lint/build. Browser smoke is the final confidence check, not a substitute for automated tests.
- Use safe test data, inspect console errors, and include a mobile-width check for frontend work.
- Run project-memory checks when project memory changes.
- Always run `git diff --check` and inspect the final branch, status, diff, staged files, and temporary artifacts.
- Never claim completion when required validation has not run. Report skipped or blocked checks explicitly.

## Completion Report

Report the exact touched files, test commands and counts, lint/build results, browser-smoke coverage, database safety, temporary-artifact cleanup, `git diff --check`, current branch/status, staged/committed state, and any unresolved concern.
