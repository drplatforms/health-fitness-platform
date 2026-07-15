# Developer Delivery Workflow Contract

`current_workflow_contract.md` is the canonical workflow. This supporting contract defines practical delivery expectations for bounded Health & Fitness Platform implementation work.

## Before editing

- Read the user/Architecture handoff, `AGENTS.md`, `README.md` in this directory, `current_state.md`, `current_workflow_contract.md`, the active milestone, and affected contracts.
- Verify the branch, exact starting commit, recent history, full status including untracked files, and relevant diffs.
- Treat the working tree as authoritative. Preserve existing work and stop on a material branch/base/scope conflict.
- Establish database safety before Python or runtime commands. Use temporary databases or copies; never allow automated work to initialize or mutate the real `fitness_ai.db`.

## Implementation and evidence

- Change only authorized files and reuse existing contracts/services/helpers.
- Update project memory in the same branch for meaningful behavior, architecture, workflow, or accepted-status changes.
- Run targeted tests selected from `validation_matrix.md`, expanding based on risk.
- Run lint/build checks for touched areas. UI work requires production-mode browser smoke on Next.js port `3100`; docs/tooling-only work normally does not.
- Inspect browser console state and mobile width when UI smoke is required.
- Always inspect `git diff --check`, final status, full unstaged diff, untracked files, staged files, database safety, and temporary artifacts.

## Git closeout boundary

Codex does not stage, commit, push, merge, or snapshot unless the user explicitly authorizes the applicable action. Architecture reviews the actual diff and evidence before acceptance. Staging is explicit; helper commands must never hide it.

After acceptance, the normal closeout is feature commit/push, merge, ancestry verification, merged-main validation, push main, and an external snapshot from clean validated `main`. Snapshot files belong in:

```text
C:\projects\fitness_ai_external\snapshots
```

Linux at `~/projects/fitness-ai-platform` remains secondary. Linux sync is optional and task-specific; it is not coupled automatically to snapshot creation.

The hard-stop and ancestry details in `developer_delivery_workflow_script_safety_addendum_v1.md` remain applicable where they do not conflict with `current_workflow_contract.md`.
