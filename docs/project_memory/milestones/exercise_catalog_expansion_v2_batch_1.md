# Exercise Catalog Expansion v2 — Batch 1

Status: implementation complete; Architecture acceptance pending.

## Scope delivered

- Expanded the curated exercise catalog from 240 to exactly 300 entries.
- Preserved the existing 240 entries and their order, then appended 60 provider-grounded entries as one explicit batch.
- Added complete catalog, taxonomy, prescription-measurement, instruction, visual-identity, and reviewed provider-media metadata for every new entry.
- Reused the existing exercise types, movement patterns, equipment tokens, difficulty values, taxonomy families, base movements, variant keys, and variant-extension keys.
- Added no schema, route, dependency, UI, persistence-contract, recommendation, or generation-behavior changes.

## Provider acquisition and review

- Source endpoint: `https://oss.exercisedb.dev/api/v1/exercises`
- Developer-time inventory inspected: 1,500 unique provider rows.
- Final admitted rows: 60.
- Provider GIF decisions for Batch 1: 0 approved; all 60 are `provider_media_not_approved` because AscendAPI GIF expansion was intentionally retired from the current product direction.
- Existing reviewed provider mappings preserved: 46.
- Final reviewed provider mappings: 46.
- Two provisional candidates were rejected during frame review because their media did not represent the intended admitted identity; they were replaced before runtime admission.
- The authoritative row-by-row evidence is in `docs/project_memory/catalogs/exercise_catalog_expansion_v2_batch_1_matrix.csv`.

Provider metadata and media remain non-authoritative presentation evidence. Backend-owned catalog, taxonomy, prescription, instruction, validation, and deterministic fallback remain authoritative. Animation/provider-media expansion is no longer an active product direction.

## Final reconciliation

- Curated catalog entries: 300.
- Batch 1 entries: 60.
- Taxonomy rows: 300.
- Unique visual identities: 291.
- Prescription-measurement rows: 300.
- Instruction rows: 300.
- Reviewed provider mappings: 46.
- New Batch 1 provider GIF mappings: 0.
- The 60 new exercises rely on independently available local media where present and written-instruction fallback everywhere else; the existing 46 mappings remain dormant legacy/prototype infrastructure.

All 60 additions default to `reps` and allow only `reps`, leaving the existing multi-measurement and distance-enabled cohorts unchanged.

## Deterministic utilization diagnostic

The diagnostic used a disposable database and 12 variation indices across quick, standard, and full workout sizes.

- Total active exercises: 300.
- Home-gym equipment eligible: 286.
- Generator eligible: 273.
- Unique selected in the sweep: 65.
- Equipment-eligible but absent from candidate options: 18.
- New batch generator eligible: 60 of 60.
- New batch visible to Dustin's home-gym equipment profile: 49.
- New batch commercial/machine-oriented or otherwise outside that profile: 11.
- New batch entering filtered home-gym candidate pools: 49.
- New batch selected in the sweep: 8.

The 11 entries outside the home-gym profile are Cable-Assisted Nordic Curl plus the ten machine/assisted-machine entries. This is intentional catalog breadth, not a change to Dustin's equipment constraints.

## Validation

- Focused Ruff check over every touched Python runtime, tool, and test file: passed.
- Read-only baseline audit against `9940d39`: the first 240 catalog, taxonomy, measurement, and instruction rows plus the first 46 provider mappings match exactly.
- Final affected pytest slice: 108 passed in 58.97 seconds.
- Batch-specific cross-layer evidence contract: included in the affected slice and passed.
- Specialized utilization coverage: 2 passed in 13.27 seconds during the focused rerun; the same tests also passed in the final 108-test slice.
- Project-memory validation: 603 passed, 44 pre-existing warnings, 0 failures.
- Full repository suite: not run; repository policy prohibits it for this mechanical content expansion.
- Browser smoke: not applicable because no frontend or UI behavior changed.

## Database safety incident

An existing eligibility test lacked a pytest-owned database fixture. During the first affected-slice run it invoked the diagnostic against `fitness_ai.db`, changing the canonical database fingerprint. No exact pre-run database copy was available, so the binary file was not destructively replaced or logically rewritten without user direction.

The test now redirects to a pytest-owned temporary database, and the diagnostic trace wrapper is compatible with the current selection signature. The canonical database SHA-256 remained stable at `1186BAC75B2F057988C4310ACD0D071F2320D4A05A1400AD98ADFDB46DDE90B4` throughout all subsequent focused and final validation. Exact restoration of the prior canonical database remains an explicit closeout concern requiring user direction.

## Instruction accuracy correction

The accepted Batch 1 catalog data remains unchanged. Ten new entries now use dedicated instruction templates when their physical setup conflicts with a shared generic template: Dumbbell Push Press, Dumbbell Cuban Press, Dumbbell Seated Calf Raise, Machine Seated Calf Raise, Barbell Hack Squat, Standing Cable Crunch, Band Step-Up, Low Cable Fly, Self-Assisted Nordic Curl, and Cable-Assisted Nordic Curl.

The correction preserves all pre-Batch-1 instruction outputs and the exact 300-row seed invariant. Focused instruction coverage, instruction API, and Batch 1 cross-layer tests passed: 31 passed in 6.65 seconds.

Final instruction leakage correction: thirteen additional Batch 1 exercises now use dedicated profiles for their admitted setup or movement: Archer Push-Up, Pistol Squat, Single-Arm Dumbbell Shoulder Press, Single-Arm Dumbbell Bench Press, Dumbbell Single-Leg Calf Raise, Reverse-Grip Incline Dumbbell Row, Bench-Supported Dumbbell Rear Delt Row, Cable Reverse Crunch, Resistance Band Seated Row, Band Single-Leg Calf Raise, Band Reverse Fly, Machine Reverse Fly, and Assisted Triceps Dip. This preserves the original 240 instruction outputs and the already-corrected ten Batch 1 profiles.

The focused instruction coverage, instruction API, and Batch 1 cross-layer slice passed: 32 passed in 4.43 seconds.

After this correction session, the read-only canonical database SHA-256 was `62FA75B7F3DE1207C6005294384EAE92281D7D0043D73F928FF247E697DA4025`, which differs from the earlier recorded fingerprint. This session did not capture a pre-run fingerprint, so the timing and cause cannot be attributed; no database restoration or rewrite was attempted.

## Acceptance boundary

Architecture should verify:

1. the 60 admissions and evidence decisions are acceptable;
2. the 49 home-gym / 11 commercial-or-other split is intentional;
3. the utilization diagnostic breadth is acceptable without generator behavior changes; and
4. how to handle the canonical database safety incident before milestone acceptance.
