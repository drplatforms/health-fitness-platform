# Weekly Training Planner v1

Status: implemented on `feature/weekly-training-planner-v1`; awaiting Architecture review and acceptance.

Base: `main` at `7685843`

## Delivered behavior

- Persists one user-owned weekly plan per Monday-normalized week with exactly seven day rows.
- Supports one through six selected training weekdays and persists deterministic directive snapshots for the authorized frequency sequences.
- Represents rest days explicitly and derives planned, today, selected, in-progress, completed, missed, extra-workout, and rest states from persisted execution truth.
- Allows future-day edits while preserving protected past, selected, in-progress, and completed day snapshots atomically.
- Supplies an optional scheduled-day directive to the existing deterministic workout generator without changing the generic no-plan path.
- Suppresses the day-of preview on scheduled rest days until the user chooses **Train anyway**; the override does not rewrite the weekly plan.
- Adds the compact Week planner, Today/Week navigation, weekly context line, and browser-local dated day-of requests while preserving the live unpinned URL.

## Persistence and ownership

- Added `weekly_training_plans` and `weekly_training_plan_days` through the existing additive SQLite initialization path.
- Weekly rows retain source and directive provenance; protected day snapshots are not silently regenerated during future edits.
- Workout selection, execution, progression, recovery, sizing, variation, and substitution remain owned by their existing services.

## Validation evidence

- Weekly planner service/API/integration: `22 passed`.
- Core workout/weekly regression slice: `162 passed`.
- Intelligence and persistence regression slice: `197 passed`.
- Frontend pure-helper tests: `14 passed`.
- Ruff check and format: passed.
- Frontend lint: passed.
- Production frontend build: passed.
- Production-mode browser smoke against an isolated database: passed for 1-, 3-, and 4-day creation; protected/future editing; week overview; scheduled rest suppression; Train anyway; workout sizes; variation; select/start/set logging; progression history/next target; substitution UI; historical read-only state; Light/Dark themes; desktop, 390x844, and 360px widths. Browser console errors: none.
- Full backend suite: `2647 passed, 4 failed`; the four failures are pre-existing developer-workflow/project-state baseline mismatches that expect old commit/doc state.

## Safety and open review notes

- Browser smoke used a copied temporary database and isolated ports; all temporary processes and artifacts were removed.
- The canonical `fitness_ai.db` hash changed during the full pytest run from `22a508484fd03750b8043979f11dd872c3b0a68264671df304e0c2c81259ee35` to `452d49b6080c37683072e8ffb2d822cd0e6978a245679a0e14a8b08827284c2f` because a pre-existing test path initialized the two new empty weekly tables on the real database. No weekly plan/day rows were inserted. The isolated browser smoke did not change that second hash further. No automatic rollback was attempted because no pre-run copy existed.
- Browser regression smoke exposed two existing substitution presentation/state concerns: replacement equipment badges retain the original exercise equipment, and the start transition clears the local substitution overlay. These are recorded for follow-up and were not expanded into this milestone.

## Acceptance boundary

This file records implementation evidence only. It does not mark the milestone accepted, stage files, create a commit, push, merge, or authorize a snapshot.
