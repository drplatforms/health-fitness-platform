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
2. Read `docs/project_memory/current_truth.json`, the active milestone file, and any architecture contracts the work affects. Read `current_state.md` only when historical chronology is relevant.
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

## Projectmem

- Projectmem is an optional supplemental context accelerator. Explicit user authority, the active Architecture handoff, this file, canonical project memory, and repository truth outrank Projectmem-local instructions when they conflict.
- Retrieve selectively. Write rarely.
- When Projectmem MCP tools are available, start with `get_instructions`, `get_summary`, and `get_project_map`. Use focused `get_context` only when a specific unresolved question justifies it, then read the current handoff, `docs/project_memory/current_truth.json`, and directly relevant canonical project-memory files.
- Write only durable cross-session negative knowledge, safety incidents, recurring non-obvious failure modes, or explicit supersessions. Do not log routine command failures, retries, attempts, fixes, successful edits, or test results already represented by Git or tests.
- Do not run `pjm init`, install Projectmem hooks, or start the Projectmem watcher unless an authorized tooling milestone explicitly allows it.

## Operator Command Contract

- Dustin operates consequential repository phases through complete copy/paste Windows PowerShell blocks supplied by Architecture.
- Reuse the canonical Architecture command template when one exists. Do not invent an alternate routine Git or closeout sequence without stating the technical reason.
- Provide one complete phase at a time for consequential operations. Never split dependent PowerShell syntax across messages and never provide a detached `else`.
- Any consequential paste block that depends on `throw`, `$LASTEXITCODE`, or another stop-on-failure guard must execute as one PowerShell script block such as `& { ... }`, so a failure terminates the entire pasted phase instead of allowing later commands to continue.
- Use literal here-strings when writing Markdown that contains backticks.
- Stage exact reviewed files only. Never use `git add .` or `git add -A`.
- Stop and diagnose any failed validation, staging, commit, push, checkout, pull, merge, or safety check. Verify each consequential operation before continuing.
- Codex does not perform Architecture Git closeout: no staging, committing, pushing, merging, or snapshot creation without separate explicit authority.

## Validation

- Validation is targeted and risk-based by default. Use the narrowest credible validation set for the actual change and select targeted pytest slices from `docs/project_memory/validation_matrix.md`.
- Full repository test-suite execution is exceptional, not a default milestone or closeout requirement. Codex may run the full suite only when Architecture explicitly authorizes it and records a concrete cross-cutting risk justification. Milestone closeout by itself is never sufficient justification.
- Mechanical data/content expansions should use focused affected-feature tests plus only the relevant static, build, and smoke checks.
- Frontend-only work should use affected frontend tests, lint/build, and required browser smoke.
- Bounded backend work should use affected service/API tests plus the nearest credible regression slices. Broader category suites are reserved for shared contracts or genuinely cross-cutting behavior.
- When a broad or full suite is genuinely useful but Codex does not need to reason through its execution, prefer running it outside the expensive Codex implementation session where practical.
- Run lint and build checks for touched areas.
- UI-impacting work requires production-mode browser smoke after lint/build. Browser smoke is the final confidence check, not a substitute for automated tests.
- Use safe test data, inspect console errors, and include a mobile-width check for frontend work.
- Run project-memory checks when project memory changes.
- Always run `git diff --check` and inspect the final branch, status, diff, staged files, and temporary artifacts.
- Never claim completion when required validation has not run. Report skipped or blocked checks explicitly.

## Completion Report

Report the exact touched files, test commands and counts, lint/build results, browser-smoke coverage, database safety, temporary-artifact cleanup, `git diff --check`, current branch/status, staged/committed state, and any unresolved concern.

## Mandatory Projectmem-first orientation

When Projectmem MCP is available, Codex must use Projectmem before broad repository or project-memory inspection.

Required initial sequence:

1. `get_instructions`
2. `get_summary`
3. `get_project_map`

Use focused `get_context` only when a specific unresolved question justifies the additional read.

After that, read only the active handoff and the minimum directly relevant canonical project-memory, implementation, and test files.

Do not manually reread the broad `docs/project_memory` corpus by default.

If Projectmem is unavailable or fails, report that immediately and fall back to targeted canonical reads.

Every Codex completion report must include:

```text
Projectmem orientation report:
- MCP available: yes/no
- Projectmem tools used:
- Direct canonical project-memory files read:
- Broad repository scan performed: yes/no
```
