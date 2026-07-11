# FNDDS WWEIA Header Compatibility v0.1

Latest accepted application source of truth remains `main` at `e229600 Close USDA generic source expansion memory`.

Compatibility implementation branch: `feature/fndds-wweia-header-compatibility-v0-1`.

Status:

```text
FNDDS_WWEIA_HEADER_COMPATIBILITY_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

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
- Nothing has been staged, committed, pushed, merged, or snapshotted.
