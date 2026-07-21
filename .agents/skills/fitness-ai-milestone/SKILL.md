---
name: fitness-ai-milestone
description: Implement and validate scoped work in the Health & Fitness Platform repository with lightweight safety rails.
---

# Fitness AI Milestone

Work from the user's request and the repository itself.

## Workflow

1. Read the applicable `AGENTS.md`.
2. Inspect the current branch, Git status, and only the code needed for the task.
3. Briefly state what you found and your intended approach, then proceed unless there is a meaningful conflict.
4. Implement the smallest sound solution.
5. Run targeted validation based on actual risk.
6. Inspect the final diff, clean temporary artifacts, and report the result.

## Rules

- Do not read project memory, validation matrices, milestone history, or Projectmem by default. Use them only when explicitly requested or when a concrete ambiguity/conflict requires them.
- Do not perform routine Projectmem orientation or logging for ordinary feature work.
- Let repository exploration determine which files need to change. Avoid broad scans and unrelated refactors.
- Preserve unrelated and uncommitted work. Never reset, restore, discard, or clean work you did not create.
- Reuse existing components, services, contracts, helpers, and data shapes where practical.
- Treat an explicit implementation request from the user as authorization for that scoped work unless stated otherwise.
- Use focused tests for affected behavior. Run lint/build and browser smoke only when relevant to the changed surface and risk.
- Do not run project-memory checks unless project-memory files changed. Do not run the full repository suite unless the change is genuinely cross-cutting or explicitly requested.
- Never mutate, restore, or replace the user's real `fitness_ai.db`; use disposable data for automated mutation.
- Do not merge to `main`. Stage, commit, or push only when explicitly requested. Never force-push or rewrite history without explicit authorization.
- Report what changed, validation performed, any real unresolved issue, and relevant Git status. Do not dump exhaustive command logs unless asked.
- Never claim validation that was not actually performed.
