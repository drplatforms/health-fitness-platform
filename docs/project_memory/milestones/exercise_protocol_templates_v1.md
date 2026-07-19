# Exercise Protocol Templates v1

Branch: `feature/exercise-protocol-templates-v1`
Baseline: `main` at `1d2f143` (`Merge exercise prescription measurement types v1`)

## Objective

Represent the accepted programming protocol separately from canonical physical
exercise identity. This is additive metadata only: the existing 16 protocol-
bearing exercise identities, taxonomy, measurement semantics, and workout
behavior remain unchanged.

## Registry and links

- The immutable repository-owned registry has exactly nine slugs: `intervals`,
  `steady_state`, `tempo`, `pause`, `easy`, `hill_intervals`, `recovery`,
  `easy_intervals`, and `cadence_drill`.
- It carries high-level display names and descriptions only; no numeric or
  prescriptive parameters are represented.
- The production manifest has exactly 16 explicit canonical-name links. Counts
  are tempo 4; intervals/easy/hill_intervals/recovery 2 each; and
  steady_state/pause/easy_intervals/cadence_drill 1 each.
- Runtime does not read the accepted taxonomy or measurement audit artifacts and
  does not infer protocol links from exercise names.

## Persistence and reads

- `exercise_catalog_protocols` is a one-to-one stable-ID projection keyed by
  `exercise_id` with a declared FK to `exercise_catalog_exercises`.
- Seeding requires a pre-established catalog, validates the complete manifest
  before protocol writes, resolves exact names, atomically replaces all rows,
  removes stale rows, rolls back on failure, is idempotent, and never changes
  canonical catalog or equipment rows.
- Stable-ID reads return protocol metadata for linked exercises and `None` for
  known non-protocol or unknown IDs. Nonpositive IDs are rejected and corrupt
  persisted slugs fail explicitly.
- `GET /exercise-catalog/{catalog_exercise_id}/protocol` is an additive,
  read-only inspection endpoint. It returns 404 for unknown IDs and `protocol:
  null` for known exercises without a link.

## Boundaries preserved

- No canonical exercise ID or identity was merged, deleted, normalized, or
  rewritten.
- No generator, prescription target, provider, progression, execution,
  substitution, summary, UI, taxonomy, measurement, or form-media behavior was
  changed.
- No external API or AscendAPI integration was added.

## Validation

- Focused protocol registry, persistence, established-catalog boundary,
  stable-ID read, rollback, and API tests: 7 passed.
- Targeted catalog, taxonomy, measurement, and shared catalog-route regressions:
  86 passed total.
- Targeted Ruff check and format check: passed.
- Project-memory checker: PASS=609, WARN=38, FAIL=0; focused checker tests: 29
  passed.
- `git diff --check` and final Git inspection remain required immediately before
  Architecture source review.

## Architecture acceptance

Status: Architecture accepted after source review and corrected catalog-preservation validation.
