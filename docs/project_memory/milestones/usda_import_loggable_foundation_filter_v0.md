# USDA Import Loggable Foundation Filter v0

Last updated: 2026-07-06

## Purpose

Hotfix the USDA real-dataset directory importer so local FoodData Central CSV imports default to loggable top-level `foundation_food` rows instead of pulling mostly hierarchy/support rows during smoke imports.

## Scope

- Preserve the existing simple `--input` USDA-style CSV mode.
- Preserve extracted FoodData Central `--fdc-dir` mode.
- Default `--fdc-dir` imports to `foundation_food`.
- Add `--include-data-types` override support for review/debug imports.
- Apply `--limit` after data-type filtering.
- Preserve `source_record_id` as the USDA FDC ID.
- Preserve `fdc_id` inside `source_payload_json`.
- Preserve explicit USDA zero macro values as `0`.
- Preserve missing joined macro nutrients as `NULL` / `None`.
- Skip negative joined macro values from `food_nutrient.csv` so malformed source rows do not abort the import or store negative macros.

## Boundaries Preserved

- No food search UI.
- No food logging UI.
- No canonical-food promotion logic.
- No USDA full dataset or generated SQLite DB files committed.

## Validation Target

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
