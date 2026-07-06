# USDA Food Data Import Foundation v0

Status:

```text
USDA_FOOD_DATA_IMPORT_FOUNDATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the first repeatable local USDA FoodData Central import path so future nutrition logging can build from USDA-backed local source rows instead of a live external API or committed bulk dataset.
```

What was added:

- Extended the existing `raw_food_source_records` table to preserve USDA-ready metadata:
  - `data_type`
  - `gtin_upc`
  - `serving_size`
  - `serving_size_unit`
  - `calories_per_100g`
  - `protein_g_per_100g`
  - `carbs_g_per_100g`
  - `fat_g_per_100g`
  - `import_batch`
- Added `models/usda_food_data_models.py`.
- Added `services/usda_food_data_import_service.py`.
- Added `scripts/import_usda_food_data.py`.
- Added the tiny checked-in fixture at `tests/fixtures/usda/sample_foods.csv`.
- Added focused importer tests at `tests/test_usda_food_data_import.py`.
- Added ignored local data paths for full USDA downloads.

Discovered existing nutrition persistence:

- Legacy daily macro rollups still read from `foods`, `food_nutrients`, and `food_entries`.
- The app already has a two-layer food foundation:
  - raw/source food records
  - curated canonical app-facing foods
- Existing `tools/import_food_catalog.py` is a staged review importer only and does not populate the runtime database.

Schema/table/model decision:

- Reused and extended `raw_food_source_records` instead of inventing a second raw-source subsystem.
- Kept canonical foods separate from raw USDA import rows.
- Preserved the two-layer doctrine:
  - raw imported source rows can be large and local
  - canonical app-facing foods stay curated and controlled

Ignored USDA data path:

```text
data/usda/
data/imports/usda/
```

Importer command shape:

```powershell
.\.venv\Scripts\python.exe .\scripts\import_usda_food_data.py --input .\tests\fixtures\usda\sample_foods.csv --db-path .\tmp\usda_import_test.db
```

Fixture path:

```text
tests/fixtures/usda/sample_foods.csv
```

Full USDA dataset handling:

- Full USDA downloads are intentionally not committed.
- The importer is designed for local CSV input outside Git.
- The checked-in fixture is tiny and test-only.

What comes next:

- Add a small raw-source search/inspection tool if Architecture wants easier local validation.
- Decide the next promotion step from USDA raw-source rows into curated canonical foods.
- Later connect curated canonical foods, serving units, and logging contracts without exposing raw imported rows directly to users.

Remaining risks:

- This milestone stores USDA-backed raw rows locally but does not yet promote them into canonical search/logging.
- Large real-world USDA imports may need future performance tuning beyond this v0 importer path.
- Brand owner is currently preserved through the existing raw-source brand field rather than a separate dedicated `brand_owner` column.
