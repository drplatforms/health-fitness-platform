---
name: fitness-ai-milestone
description: Execute authorized Fitness AI repository milestones from handoff through validation and clean closeout. Use when implementing, resuming, or verifying scoped work in the fitness_ai repository, especially when branch safety, project memory, targeted tests, safe browser smoke, database protection, and exact completion reporting are required.
---

# Fitness AI Milestone

Read `docs/project_memory/current_state.md`, the active milestone memory, and `docs/project_memory/validation_matrix.md` before editing.

## Standard Loop

Follow this sequence:

```text
inspect
→ compare current work to milestone scope
→ implement only approved scope
→ run targeted validation
→ run lint/build where relevant
→ run browser smoke using safe data
→ clean temporary artifacts
→ inspect diff
→ report exact results
→ stop without staging or committing
```

1. Inspect the branch, latest commit, status including untracked files, staged files, and relevant diffs.
2. Confirm the handoff matches current project memory, expected files, boundaries, and base branch.
3. Preserve existing work and reuse current services, contracts, and helpers.
4. Implement only the authorized behavior and files. Avoid broad refactors.
5. Select targeted checks from `docs/project_memory/validation_matrix.md`; add tests required by the milestone's actual risk.
6. Run lint/build for touched areas. Run production browser smoke for UI work and for milestones that explicitly require runtime confidence.
7. Use a temporary database or copy for automated smoke. Never mutate the real `fitness_ai.db`.
8. Remove temporary scripts, databases, logs, reports, and fixtures.
9. Run `git diff --check`, inspect exact changed and staged files, and confirm database safety.
10. Report exact commands, counts, smoke coverage, cleanup, Git status, and anything not validated. Do not stage or commit unless separately authorized.

## Interrupted Session Recovery

- Resume from the existing working tree; do not restart blindly.
- Inspect branch, status, staged files, and diff before taking action.
- Do not overwrite, restore, reset, discard, or clean partial work.
- Compare completed requirements and validation evidence with the milestone checklist.
- Finish only missing, broken, or unverified work.
- Treat unexpected overlapping changes or branch conflicts as reportable conditions. Work around unrelated changes when safe; stop when the milestone cannot be isolated.

Never claim completion while required validation is missing or temporary artifacts remain.
