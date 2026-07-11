# FNDDS WWEIA Header Compatibility v0.1

Current source of truth: `main` at `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.

Feature implementation commit: `75486d8 Support current FNDDS WWEIA header`.

Status:

```text
FNDDS_WWEIA_HEADER_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

## Closeout

- Accepted merge: `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.
- Feature implementation: `75486d8 Support current FNDDS WWEIA header`.
- Importer and inventory regression: `70 passed`.
- Import and promotion safety regression: `49 passed`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Ruff checks passed.
- Production browser smoke passed using a temporary database.
- Official FNDDS 25-row import inserted `25` rows and reran as `0` inserts plus `25` updates.
- Canonical foods and canonical source links remained unchanged.
- The real `fitness_ai.db` was not read or mutated.
- Milestone is accepted, merged, and closed.

## Purpose

Restore compatibility between the accepted generic FNDDS importer/inventory contract and the current official WWEIA category-table header without expanding catalog behavior.

## Implemented Scope

- Both the importer and the read-only inventory service accept `wweia_food_category` and `wweia_food_category_code`.
- The current official input alias resolves to the stable internal value and raw source-payload key `wweia_food_category_code`.
- If both headers exist, matching normalized non-empty values are accepted; one empty and one non-empty value uses the non-empty value; conflicting non-empty values fail clearly.
- The WWEIA description header remains required. Neither accepted code header, a blank resolved code, or duplicate resolved code fails clearly.
- FNDDS category lookup and output report keys remain unchanged. Foundation and SR Legacy category paths remain unchanged.
- No public payload key named `wweia_food_category` is preserved.

## Official Compatibility Smoke

- Reused the retained official FNDDS extracted release under `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10`.
- Confirmed the actual WWEIA header: `wweia_food_category,wweia_food_category_description`.
- First 25-row default-profile import into an external scratch database: `25` processed, `25` inserted, `0` updated; all rows used `survey_fndds_food`.
- Rerun using the same batch: `25` processed, `0` inserted, `25` updated; raw row count remained `25` with no duplicate source identities.
- All 25 rows had a food code, WWEIA category number, stable WWEIA category code, and category description. No raw payload exposed the input-only alias key.
- Macro values were nonnegative or null. Canonical food and canonical source-link counts remained zero.
- The external scratch database was removed after validation.

## Validation

- Importer/inventory regression: `70 passed`.
- Import/promotion safety regression: `49 passed`.
- Ruff check and touched-file Ruff format checks passed.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Production browser smoke used only `tmp/fndds_wweia_header_compatibility_smoke.db`. Today, Nutrition, canonical food search, and Workout loaded; console errors were zero; Today and Workout had no horizontal overflow around 390px; no data-changing control was used.
- The temporary database, launcher, logs, bytecode, and dedicated backend/frontend processes were removed.

## Boundaries

- No schema, migration, generic source-profile, food/nutrient streaming, FNDDS survey join, category semantics, source identity, transaction, canonical-promotion, CLI, frontend, dependency, or real `fitness_ai.db` change was made.
- The implementation originally stopped unstaged and uncommitted; it was later committed as `75486d8` and merged to `main` as `34d4a59`.
