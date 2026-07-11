# USDA Generic Source Expansion v0

Current source of truth: `feature/usda-generic-source-expansion-v0` based on accepted `main` at `d424a83`.

Status:

```text
USDA_GENERIC_SOURCE_EXPANSION_V0_IMPLEMENTATION_COMPLETE
```

## Purpose

Expand the raw USDA FoodData Central source layer to the three generic food-composition sources without changing canonical promotion or public search behavior.

## Implemented Scope

- Changed the FDC directory default profile to `foundation_food`, `sr_legacy_food`, and `survey_fndds_food`.
- Normalized documented USDA display aliases to those stable internal keys while retaining normalized matching for explicit review/test overrides.
- Preserved the original USDA `food.csv` value as `source_data_type` and the stable key as `normalized_data_type` in raw source payloads.
- Streamed `food.csv` with header validation, normalized-type filtering, selected-ID validation, duplicate rejection, and post-filter limit handling.
- Streamed `food_nutrient.csv` once, skipped unrelated FDC IDs before nutrient-detail parsing, and retained only calories, protein, carbohydrates, and fat for selected rows.
- Preserved explicit zero macro values and represented missing macros as `None`.
- Avoided opening `branded_food.csv` unless `branded_food` is explicitly included.
- Added optional FNDDS metadata support through `survey_fndds_food.fdc_id -> wweia_category_number -> wweia_food_category_code -> wweia_food_category_description`.
- Preserved FNDDS food code and WWEIA category number/code in the raw source payload; missing optional metadata leaves category unset.
- Kept Foundation and SR Legacy category resolution on `food.food_category_id -> food_category.id`.
- Added per-data-type processed counts to import summaries and CLI output.
- Added inventory macro coverage by raw data type and FDC category counts by generic source type while retaining the prior Foundation-only compatibility field.

## Persistence And Safety Boundaries

- Source identity remains `source_name + FDC ID`.
- Reimport updates existing raw source records without creating duplicates.
- Import validation and persistence remain transactional; failed validation does not partially mutate raw records.
- Existing canonical foods and source links are not changed by import or inventory.
- The inventory database connection remains read-only.
- No schema, migration, dependency, canonical promotion, public search, food logging, nutrition calculation, workout, provider, or frontend runtime change was added.
- The real `fitness_ai.db` was not used or mutated during validation.

## Synthetic Fixture

The compact FDC fixture contains one Foundation row, two SR Legacy rows, two Survey/FNDDS rows, one Branded row, and one Experimental row. It includes synthetic Standard Reference and WWEIA categories, complete and missing macro profiles, an explicit-zero macro, unrelated nutrient rows, and optional branded metadata. The values are test data and are not represented as real USDA nutrition facts.

## Validation

- Importer and inventory tests: `58 passed`.
- Food import and promotion regression tests: `44 passed`.
- Canonical logging, search, and normalization confidence tests: `70 passed`.
- Ruff check and touched-file Ruff format checks passed.
- Project-memory validation completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- Scratch default import processed `5` rows: `foundation_food=1`, `sr_legacy_food=2`, and `survey_fndds_food=2`.
- Scratch import excluded Branded and Experimental rows, left canonical foods and source links unchanged, and reran as `0` inserts plus `5` updates without duplicates.
- Scratch inventory reported the expected grouped macro and source-appropriate category counts.
- No extracted full local FoodData Central CSV directory was available; the optional full-dataset validation was not run and no dataset was downloaded.
- Production browser smoke used only `tmp/usda_generic_source_expansion_browser.db` with dedicated backend/frontend processes. Today, Nutrition, canonical food search/logging UI, and Workout loaded; no user data was created, edited, deleted, or completed; the browser console had zero errors; and Today/Workout had no horizontal overflow around 390px.
- Scratch and browser databases, reports, launcher, logs, bytecode, and dedicated processes were removed after validation.

## Closeout State

- Project-memory checker and checker tests passed.
- `git diff --check` and the read-only milestone status helper remain part of final repository validation.
- Nothing is staged, committed, pushed, merged, or snapshotted for this milestone.
