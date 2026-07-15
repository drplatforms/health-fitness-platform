# Personal Custom Foods Contract and Persistence v1

## Status

```text
PERSONAL_CUSTOM_FOODS_CONTRACT_PERSISTENCE_V1_ACCEPTED_MERGED_AND_CLOSED
```

## Git State

- Feature implementation: `89c1d58 Add personal custom food persistence`.
- Accepted merge: `4da8672 Merge personal custom foods contract and persistence v1`.
- Accepted on local `main`; push and snapshot remain pending.

## Scope

- Add user-owned personal-food identity and immutable revision persistence.
- Support nutrition-label and per-100g inputs with deterministic normalization and unknown nutrients preserved as `NULL`.
- Support grams and default-serving logging against the current revision at transaction time.
- Store exact personal-food identity, revision, display-name, and known nutrient snapshots on each log entry.
- Preserve existing canonical and legacy logging behavior and Target-vs-Actual compatibility through one internal immutable legacy food row per revision.
- Add user-scoped create/read/list/search/revise/archive/restore/log API contracts.
- Hide internal personal-food legacy rows from global legacy search.

## Safety And Ownership

- Every personal-food operation validates the owning user.
- Another user may not read, search, revise, archive, restore, or log a personal food.
- Archived foods remain historically readable but are hidden from default search and cannot be newly logged.
- Creation and revision are multi-table atomic transactions; partial identities, revisions, legacy rows, or nutrient rows must not survive failure.
- Read/search operations must not initialize or alter schema.

## Non-Goals

- No recipes, saved meals, barcode/OCR/import workflow, AI nutrition generation, AI meal planning, frontend UI, workout behavior, report behavior, provider behavior, or real database mutation.

## Validation

Completed automated validation:

- Personal-food schema, service, logging, and API tests: `73 passed`.
- Existing canonical logging, edit/delete, serving-unit, search, recents, Target-vs-Actual, trend, and API smoke regression slice: `143 passed`.
- Prior final-correction full repository test suite: `2496 passed`; the narrow resolved-serving underflow handoff did not require a full rerun.
- Touched-file Ruff check and format check passed for all ten milestone Python files. Formatting was limited to milestone-touched files.
- Python compile checks cover the nutrition route and both personal-food services.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; project-memory checker tests: `29 passed`.
- Underflow-correction validation ran from an isolated temporary source mirror with no live database. Personal-food tests passed: `73`; nutrition regression tests passed: `143`. The prior final-correction full repository suite passed: `2496`.

Architecture correction results:

- The existing-database migration now creates referenced personal-food tables before adding nullable provenance columns with inline `REFERENCES` clauses. A pre-milestone populated fixture proves both foreign keys are present, the existing log row is unchanged, and initialization remains idempotent.
- Nutrition-label normalization validates each derived per-100g value after arithmetic. Overflowing calories and protein are rejected before any personal identity, revision, internal legacy food, or nutrient row can persist.
- Personal-food logging reuses the canonical 5,000 g ceiling for direct grams and resolved serving amounts. Exactly 5,000 g is accepted; 5,000.001 g, 5,001 g, and a serving resolving to 5,001 g are rejected without a log row.
- Pydantic pre-coercion validation rejects booleans for create/revision nutrition numbers and log identity/amount fields. Normal integer and floating-point JSON inputs remain supported, and failed requests create no personal identity, revision, internal legacy nutrient data, or food entry.
- Direct service calls require a positive integer personal-food ID for get, revise, archive, restore, and log operations; `True` cannot resolve to identity `1`.
- Logging validates every scaled calorie/protein/carbohydrate/fat snapshot after arithmetic. Overflowing calories and protein roll back without an entry, while a high but finite snapshot remains supported.
- Serving-based logging validates resolved grams after multiplication. Tiny positive serving grams and quantity that underflow to `0.0` produce a public-safe validation error and no `food_entries` row; normal serving logs and the 5,000 g ceiling remain unchanged.

Database-safety incident and authorized recovery:

- The ignored real `fitness_ai.db` had modification time `2026-07-14T19:48:29.4922147-04:00` and SHA-256 `290C2F73DD731E5F8976B50CCB2CAB28D66810CDC4843BF147DB9D69A60AEACB` when inspected.
- A SQLite read-only schema probe confirmed that both new personal-food tables, all three new `food_entries` provenance columns, and all three new indexes were present in the real database.
- `personal_foods` and `personal_food_revisions` each contained zero rows, and no existing `food_entries` row had a non-null personal-food provenance value.
- Architecture authorized preserving the current user data and reversing only the empty additions. External recovery evidence and backups are retained at `C:\projects\fitness_ai_external\db_recovery\personal_custom_foods_schema_cleanup_20260714_203741`.
- Filesystem and SQLite API backups matched the pre-cleanup logical state. Only `personal_foods`, `personal_food_revisions`, their three named indexes, and the three nullable `food_entries` provenance columns were removed in one `BEGIN IMMEDIATE` transaction.
- Pre-existing table counts and data fingerprints matched before and after. `integrity_check` remained `ok`. The exact 34-row pre-existing foreign-key violation set remained unchanged with SHA-256 `E8B9DF295C8DAA60E5B5E41AB0BAA15605B216A1D4B207412EB6EB0993F1F133`; no legacy violations were repaired or altered.
- The live database hash changed from `290C2F73DD731E5F8976B50CCB2CAB28D66810CDC4843BF147DB9D69A60AEACB` before cleanup to `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38` after cleanup, then remained unchanged throughout isolated test revalidation.

Browser smoke is deferred to Personal Custom Foods UI v1. Before that future manual smoke, make a named backup copy of the real database, configure both backend and frontend smoke processes to use a dedicated temporary database, verify the configured database path before starting either process, and restore from the named backup only with explicit authorization if recovery is required. The backend-only milestone performs no browser smoke.

The database-safety blocker is resolved. Architecture reviewed and accepted the complete implementation and final correction diffs. Merged-main focused, nutrition-regression, full-suite, Ruff, format, compile, project-memory, and diff validation passed. The backend milestone is accepted, merged, and closed. Personal Custom Foods UI v1 is next.


## Accepted Closeout

- Feature commit: `89c1d58 Add personal custom food persistence`.
- Merge commit: `4da8672 Merge personal custom foods contract and persistence v1`.
- Merged-main personal-food focused validation: `73 passed`.
- Merged-main nutrition regression validation: passed.
- Merged-main full repository suite: passed.
- Touched-file Ruff, format, compile, project-memory, and `git diff --check`: passed.
- Real ignored database SHA-256 remained unchanged:
  `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38`.
- Browser smoke remains deferred to Personal Custom Foods UI v1.
- A separate automated review produced no usable result and was not repeated.
