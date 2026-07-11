# Workout Execution Integrity Fixes v0.1

Current source of truth: `main` at `d424a83 Merge workout execution integrity fixes v0.1`.

Feature implementation commit: `d2538d7 Fix workout execution integrity`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_d424a83_main_merge-workout-execution-integrity-fixes-v0-1.zip`.

Status:

```text
WORKOUT_EXECUTION_INTEGRITY_FIXES_V0_1_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

The milestone was accepted, merged to `main`, pushed, snapshotted, and closed.

## Purpose

Correct substitution completion attribution, planned set-number reuse, duplicate planned slots, and completion percentages above 100% without changing the workout execution schema or broader workout behavior.

## Implemented Scope

- Defined the effective planned-exercise identity as `substitution_for_planned_exercise_id` when present, otherwise `planned_workout_exercise_id`.
- Used that identity for completed and skipped exercise attribution, planned set-number allocation, duplicate validation, and frontend exercise grouping.
- Preserved substitution counts separately and kept original persisted identity fields unchanged.
- Changed planned and substitution set-number defaults to choose the smallest missing planned slot, then `max occupied + 1` after every planned slot is occupied.
- Rejected create and update operations that duplicate an execution session, effective planned exercise, and set number. Update checks exclude the row being edited, and rejected operations roll back without changing existing rows.
- Kept truly unplanned actual-row numbering independent from the planned-exercise allocator.
- Sorted saved rows within each exercise by set number so a reused missing slot displays in numeric order.
- Added `extra_set_count` to the backend summary model and frontend contract.
- Capped completion at `100.0` while preserving the truthful completed-set count and reporting extra completed sets separately.
- Added a compact neutral extra-set label below the existing Completed Sets metric.

## Integrity Boundary

- Duplicate protection is implemented in the existing service transaction boundary.
- No schema, migration, index, or database-level uniqueness constraint was added.
- The service check protects normal API create and update operations but does not claim concurrency-safe database-enforced uniqueness.

## Validation Completed

- Persistence and progression-history slice: `103 passed`.
- Workout planning, Today, rotation, and sizing slice: `128 passed`.
- Touched Python files passed Ruff lint and Ruff format checks.
- Frontend lint passed.
- Production frontend build passed, including TypeScript and route generation.
- Project-memory checker completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- `git diff --check` passed.
- The read-only milestone status helper exited successfully with only known ignored generated/local artifact warnings.

## Production Browser Smoke

- Used only `tmp/workout_execution_integrity_smoke.db` through a temporary backend bound explicitly to that path and a production frontend on dedicated ports.
- For a three-set exercise, logged sets 1-3, deleted Set 2, confirmed the form returned to `Set 2 of 3`, re-logged it, and confirmed saved rows displayed as 1, 2, 3 with no `Set 4 of 3`.
- On another exercise, deleted Set 1, confirmed the form returned to Set 1, and re-logged it without cross-exercise set-number leakage.
- Opened edit, changed a draft, cancelled it, confirmed the original row remained, then edited and saved successfully before deleting and re-logging the row.
- Applied an existing safe substitution candidate in the temporary database, logged both substitution sets, and confirmed completion review credited the planned exercise once while the replacement name remained visible.
- Added one explicit extra completed set through the temporary API setup and confirmed Completion displayed `100%`, Completed Sets displayed `12/11`, and the compact `1 extra set` label appeared.
- Confirmed completion review opened before completion and showed `Logged: 12 / 11 sets` and `Exercises: 5 / 5`.
- Confirmed zero console errors, no prohibited progression/deload/recommendation copy, and no horizontal overflow at the default desktop viewport or approximately 390px mobile width.

## Safety And Cleanup

- The real `fitness_ai.db` was not read, copied, renamed, deleted, or mutated during browser smoke.
- The temporary database, launcher, backend/frontend logs, and launcher Python cache were removed.
- Dedicated backend and frontend processes were stopped, and their ports no longer had listeners.
- No files were staged, committed, pushed, merged, or snapshotted.
