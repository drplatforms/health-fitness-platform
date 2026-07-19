# Exercise Prescription Measurement Types v1

Branch: `feature/exercise-prescription-measurement-types-v1`

Baseline: `main` at `3901d91` (`Merge exercise prescription measurement audit v1`)

Status:

```text
EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES_V1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_SOURCE_REVIEW
```

## Authority and objective

This milestone implements the accepted Exercise Prescription Measurement
Semantics Audit v1 as a backward-compatible runtime slice. The accepted audit
and matrix remain authoritative:

- `docs/project_memory/catalogs/exercise_prescription_measurement_audit_v1.md`
- `docs/project_memory/catalogs/exercise_prescription_measurement_matrix_v1.csv`

Runtime supports exactly `reps`, `duration`, and `distance`. A non-rep exercise
is represented by its real seconds or meters contract rather than fake rep/RIR
values.

## Canonical metadata and persistence

- Added immutable controlled vocabularies and
  `ExercisePrescriptionMeasurementMetadata` keyed by stable catalog exercise ID.
- Added an explicit repository-owned 240-row production manifest. Runtime does
  not parse project-memory CSV evidence and does not infer semantics by name.
- Added the one-to-one `exercise_catalog_prescription_measurements` projection
  without duplicating taxonomy, equipment, protocol, or visual identity.
- Complete-manifest validation enforces exact catalog-name coverage, stable-ID
  resolution, controlled values, defaults belonging to allowed modes, and these
  accepted invariants: 203 rep defaults, 29 duration defaults, 8 distance
  defaults, 31 multi-mode rows, and 25 distance-enabled rows using meters.
- Seeding validates before writes, atomically replaces the projection, removes
  stale rows, rolls back on failure, is idempotent, and never mutates canonical
  exercise rows.
- Stable-ID reads accept positive IDs only, return `None` for unknown IDs, and
  fail explicitly on malformed persisted JSON or controlled values.
- Startup order is database, taxonomy, measurement metadata, instructions, and
  form media.

## Contracts, migration, and legacy compatibility

- Candidate, approved, planned, actual-set, today-view, API, and frontend
  contracts now carry an explicit measurement type and nullable type-specific
  targets.
- New planned-workout schemas make rep/RIR targets nullable and add measurement,
  duration, and distance columns directly.
- Existing legacy planned schemas use a transactional SQLite table rebuild that
  preserves row IDs, values, exercise ordering, plan relationships, execution
  children, substitution children, and timestamps. It validates foreign keys,
  rolls back on failure, and is idempotent. Validation snapshots the complete
  pre-existing `foreign_key_check` result before the transaction and requires
  the post-rebuild violation multiset to match exactly; ordering is irrelevant,
  duplicate tuple counts are preserved, and any added, removed, or changed
  violation rolls back the rebuild.
- Existing planned rows remain `measurement_type = NULL` on disk and decode as
  legacy reps. No name-based backfill and no `0/0` sentinels are used.
- Existing approved-plan JSON and actual rows without measurement type continue
  to decode as reps.

## Generation and provider behavior

- Catalog metadata is the centralized source of truth for every generated
  exercise's default measurement type.
- Rep prescriptions retain their existing bounded set/rep logic. RIR remains
  nullable and is not forced where catalog applicability is not applicable or
  ambiguous.
- Treadmill and stationary-bike duration defaults use one 600-second work block;
  other duration defaults use 30 seconds per bounded work block; distance
  defaults use 20 meters per bounded work block.
- Rendering and provider context use truthful type-specific targets.
- Provider parsing retains only the explicit legacy compatibility rule that a
  missing type decodes as reps. Mixed dimensions, unsupported types, disallowed
  catalog modes, and invalid RIR combinations use the existing deterministic
  fallback path.

## Execution, summaries, progression, and substitutions

- New actual sets snapshot measurement type and the matching planned target.
  Completed rep, duration, and distance rows require a positive matching primary
  actual and reject cross-dimension values; skipped rows require none. Weight is
  independent and optional.
- Rep summary fields remain compatible and use only rep-comparable rows. Duration
  and distance add neutral comparable counts and actual-minus-planned deltas.
  Average RIR ignores non-rep and nullable-RIR rows.
- Set intelligence, progression history, today views, and post-workout review no
  longer penalize valid non-rep rows for correctly null reps/RIR.
- Duration and distance progression returns neutral insufficient-data behavior
  with `unsupported_measurement_type_for_progression_v1`; rep progression remains
  unchanged.
- Substitution candidates must allow the current planned measurement type, and
  applying a compatible replacement preserves the current type and target.
  Legacy null type behaves as reps.

## API and frontend behavior

- Existing workout endpoints and Next.js proxies were extended rather than
  duplicated.
- Planned and actual responses expose measurement type, nullable rep/RIR values,
  duration targets/actuals, and distance targets/actuals.
- Workout preview, selected, active, edit, persisted-set, and summary surfaces
  render reps, readable duration, or meters truthfully.
- Create/edit forms show exactly one primary field, optional weight, and RIR only
  for eligible rep work. Non-rep summaries avoid rep-deviation language.

## Validation evidence

- Dedicated measurement contract, seed, migration, generation/provider,
  persistence/logging/summary, progression, substitution, and API tests: 10
  passed, including unchanged unrelated-FK migration, introduced-FK rollback,
  and explicit multiset order/duplicate semantics.
- Direct read-only comparison of every production seed field to all 240 accepted
  matrix rows: passed with no missing, extra, or mismatched rows.
- Existing catalog, taxonomy, workout-plan, provider/review, migration,
  persistence, logging, and summary regressions: 256 passed.
- The corrected 256-test core and 97-test adjacent slices were rerun with the
  canonical database hashed before and after: all 353 passed, and its SHA-256
  and mtime were unchanged.
- Existing progression, progression history, set intelligence, substitution,
  today-view, and adjacent API regressions: 97 passed.
- Direct legacy planned-schema persistence migration regression: 1 passed.
- Targeted Ruff: passed.
- Frontend lint: passed.
- Frontend production build and TypeScript validation: passed; 39 routes/pages
  were collected or generated.
- Production-mode implementation smoke used a disposable database and covered
  rep work with and without RIR, duration preview/log/edit, distance
  preview/logging, type-specific persisted rows and neutral deltas, desktop,
  390 x 844 mobile layout, and a clean browser console.
- Project-memory checker and its focused regression: passed.
- `git diff --check`: passed.

Browser evidence is implementation evidence only. Architecture/user retains
feature acceptance, source review, production-smoke acceptance, and all Git
closeout ownership.

## Database-safety exception

- An early test path created the additive
  `exercise_catalog_prescription_measurements` table with 240 rows in the
  canonical `fitness_ai.db` at 2026-07-19 07:53:11 UTC before the lightweight
  catalog test double was corrected.
- Read-only attribution found the 240 projection rows as the only records with
  timestamps at that write second. The canonical planned and actual workout
  tables retain their legacy schemas, and SQLite `quick_check` is healthy.
- The corrected 256-test core and 97-test adjacent slices subsequently left the
  canonical database byte-for-byte and mtime-for-mtime unchanged, confirming
  the active test paths no longer leak writes.
- Architecture authorized a narrow recovery with the existing 34-row global
  foreign-key baseline accepted as an exception for this recovery only.
- Before cleanup, an online SQLite backup was written to
  `C:\projects\fitness_ai_external\database_backups\fitness_ai_before_measurement_projection_cleanup_20260719T104936Z.db`
  with SHA-256
  `613836377790F5ECA105A372829DD31D5D6A55B20B5F4C01A387F99EB04D1782`.
- The recovery transaction dropped only
  `exercise_catalog_prescription_measurements`. Independent canonical-versus-
  backup verification confirms the target is absent, `quick_check` is `ok`, the
  exact same 34 foreign-key violation tuples remain, protected planned/actual
  schemas are unchanged, and only the target schema object was removed.
- The immediate post-cleanup canonical database SHA-256 was
  `1B9BC83DAC8B73ADDA2C7ED24F5590B69D8B612CE90AC07E522677EC1365BFE8`.
- The feature-branch application was not restarted against the canonical
  database after cleanup. The one-use recovery script and recovery database
  sidecars were removed. Eight unrelated July 6-7 database artifacts already
  under `tmp/` were preserved as out-of-scope existing data.
- A later unrelated `daily_checkins` write advanced the canonical SHA-256 to
  `CA9961E553A1781F25B97CA2A0535CDB2DFFCF8CFCA21F500D8D8A4197E5B07A`
  before correction validation. Read-only inspection confirmed the projection
  remains absent, legacy planned/actual schemas and the exact 34-row foreign-key
  baseline remain unchanged, and all migration-correction validation preserved
  that current hash.

## Boundaries preserved

- No `duration_distance`, target ranges for duration/distance, pace, speed,
  incline, watts, heart rate, cadence, resistance, calories, telemetry, interval
  protocol segments, non-rep progression automation, historical inference, load
  redesign, catalog-wide utilization work, media changes, dependency, or parallel
  API was added.
- Production smoke used a disposable database, and temporary smoke scripts,
  databases, and logs were removed. The automated-test database exception is
  disclosed above; subsequent regression validation proved the corrected test
  path no longer mutates the canonical database.
- Nothing was staged, committed, pushed, merged, or snapshotted by Codex.

## Architecture acceptance

Status: Architecture accepted after source review, migration correction, and successful feature-branch production smoke.
