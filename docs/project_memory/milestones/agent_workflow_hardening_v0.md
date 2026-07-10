# Agent Workflow Hardening v0

Current source of truth: `main` at `4e89f27 Merge agent workflow hardening v0`.

Historical implementation base: `main` at `5d7f41d Merge workout actuals summary v0`.

Feature implementation commit: `1fa45a2 Add agent workflow hardening`.

Accepted merge commit: `4e89f27 Merge agent workflow hardening v0`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_4e89f27_main_merge-agent-workflow-hardening-v0.zip`.

Status:

```text
AGENT_WORKFLOW_HARDENING_V0_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

## Purpose

Create concise repository-native instructions and repeatable read-only guardrails so Codex can execute and resume Fitness AI milestones consistently without changing application behavior.

## Files Added Or Updated

- `AGENTS.md`
- `frontend/AGENTS.md`
- `.agents/skills/fitness-ai-milestone/SKILL.md`
- `docs/project_memory/validation_matrix.md`
- `tools/milestone_status.ps1`
- `docs/project_memory/milestones/agent_workflow_hardening_v0.md`
- `docs/project_memory/current_state.md`

## Workflow Rules Established

- Inspect branch, status, staged files, and diffs before editing or resuming.
- Compare the working tree with active milestone scope and preserve partial or unrelated work.
- Prefer existing contracts and targeted validation over parallel implementations or routine full-suite runs.
- Require safe-data production browser smoke for UI work and explicit runtime-confidence milestones.
- Protect the real database, remove temporary artifacts, inspect final diffs, and report exact evidence.
- Stop without staging or committing unless separately authorized.

## Validation

Project-memory checks, targeted Today/workout tests, frontend lint/build, and production browser smoke passed before acceptance.

- The `fitness-ai-milestone` skill passed the skill-creator `quick_validate.py` check.
- All instruction, skill, and validation-matrix references were confirmed to exist.
- `tools/milestone_status.ps1` ran from the repository root, reported normal feature work without failure, and passed working/staged diff and tracked-database checks.
- A temporary ignored `tmp/milestone_status_smoke_fixture.db` produced the expected forbidden-artifact warning without a nonzero exit; the fixture was removed immediately afterward.
- Independent review hardening added a bounded generated-directory scan that reports ignored `.next` and `node_modules` directories without descending into them, plus a blocking check for forbidden artifacts that are tracked or staged.
- Nested ignored `tmp/**/__pycache__/*.pyc` and temporary smoke-database fixtures were both detected with exit code `0`, remained byte-for-byte unchanged during inspection, and were removed afterward.
- Final review hardening replaced the remaining recursive `tmp/` scan with a depth-6, stack-based walker that skips reparse points and never descends into `.git`, `.venv`, `.cache`, `__pycache__`, `.next`, or `node_modules`.
- Bounded-walker fixtures confirmed in-depth smoke reports and loose `.pyc` files are detected, `__pycache__` and `node_modules` directories are reported without traversal, beyond-depth files are not inspected, fixture hashes remain unchanged, and normal helper execution stays nonfatal at about 1.25 seconds.
- The canonical project-memory checker completed with `590 PASS`, `58 WARN`, and `0 FAIL`; its existing test suite passed with `29 passed`.
- The Today/workout persistence, route, and view confidence slice passed with `88 passed`.
- Frontend lint and production build passed.
- Production browser smoke passed against a temporary database copy: Today and workout pages loaded, browser console errors were zero, workout controls had no unnamed interactive elements, and Today/workout had no horizontal overflow at a 390px viewport.
- The real `fitness_ai.db` was not mutated. All temporary files, generated cache files, bounded-walker fixtures, and dedicated smoke processes created by this milestone were removed.

## Boundaries

- No backend, frontend application, API contract, database schema, data, dependency, CI/CD, pre-commit, provider, or global Codex configuration changes.
- Implementation scope did not add staging, commit, push, merge, or snapshot automation.

## Closeout

- Architecture accepted the milestone.
- Feature implementation commit `1fa45a2` was merged to `main` in `4e89f27`.
- Merged `main` was pushed and snapshot `fitness_ai_snapshot_2026-07-10_4e89f27_main_merge-agent-workflow-hardening-v0.zip` was created.
- The milestone is closed.

## Follow-Up Opportunities

- Future milestones may extend the validation matrix as new product areas become active.
- CI or hook automation remains out of scope unless Architecture authorizes it separately.
- The status helper reports pre-existing ignored database, smoke, and report artifacts under `tmp/`; they were not created or removed by this milestone.
