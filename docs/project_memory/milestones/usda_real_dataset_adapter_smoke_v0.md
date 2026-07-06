# USDA Real Dataset Adapter Smoke v0

Status:

```text
USDA_REAL_DATASET_ADAPTER_SMOKE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Extend the local USDA import foundation so the repo can ingest the real extracted FoodData Central CSV directory shape without introducing a user-facing food logging system or committing bulk dataset artifacts.
```

What was added:

- Extended `services/usda_food_data_import_service.py` with a real FoodData Central directory importer that reads:
  - `food.csv`
  - `food_nutrient.csv`
  - `nutrient.csv`
  - optional `branded_food.csv`
- Kept the original simple `--input` CSV path intact for small fixtures and existing test coverage.
- Added macro derivation from USDA nutrient joins for:
  - energy kcal
  - protein
  - carbohydrate, by difference
  - total lipid (fat)
- Reused the same `raw_food_source_records` upsert path so `fdc_id`, `data_type`, normalized macros, import batch, and source payload metadata remain preserved consistently across both importer modes.
- Added `--fdc-dir` and `--limit` support to `scripts/import_usda_food_data.py`.
- Added the tiny checked-in extracted-directory fixture at `tests/fixtures/usda/fdc_csv_minimal/`.
- Expanded importer tests to cover:
  - nutrient-file joins
  - preserved `fdc_id`
  - safe behavior when `branded_food.csv` is absent
  - idempotent directory re-import behavior
  - directory import row limiting
  - CLI directory smoke behavior

Boundaries preserved:

- No fake food database, meal database, AI food parser, or long-term nutrition logging system was introduced.
- Canonical foods, search, and user-facing food logging behavior remain unchanged.
- Full USDA source downloads remain local-only and ignored by Git.
- Backend remains the owner of source metadata, macro normalization, and future promotion boundaries from raw rows to curated foods.

Importer command shapes:

```powershell
.\.venv\Scripts\python.exe .\scripts\import_usda_food_data.py --input .\tests\fixtures\usda\sample_foods.csv --db-path .\tmp\usda_import_test.db
.\.venv\Scripts\python.exe .\scripts\import_usda_food_data.py --fdc-dir .\tests\fixtures\usda\fdc_csv_minimal --db-path .\tmp\usda_fdc_import_test.db --limit 2
```

Fixture paths:

```text
tests/fixtures/usda/sample_foods.csv
tests/fixtures/usda/fdc_csv_minimal/
```

Full USDA dataset handling:

- Real USDA dataset extracts are still expected to live outside Git under ignored local paths.
- The new directory adapter is intended for extracted USDA CSV folders, not zipped archives directly.
- Optional local smoke against a real dataset remains a manual developer check and should use `--limit` first.

Remaining risks:

- Large real-dataset imports may still need future performance tuning once Architecture scopes larger local catalog promotions.
- The directory adapter preserves macro and branded metadata only where the current local raw-source schema already has a clear home.
- USDA food category enrichment is still intentionally minimal until a later curated-food promotion milestone defines how category truth should flow downstream.
