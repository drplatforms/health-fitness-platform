# Canonical Food Bulk Catalog Builder v0

Status: `CANONICAL_FOOD_BULK_CATALOG_BUILDER_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Build a repeatable backend workflow for turning many safe USDA `foundation_food` raw source rows into searchable and loggable canonical foods without importing broader USDA datasets, fabricating nutrients, or exposing raw rows directly.

## Implemented

- Added source inventory tooling at `scripts/inspect_usda_food_catalog_sources.py`.
- Added optional FDC category enrichment during `--fdc-dir` import when `food_category.csv` and `food_category_id` are available.
- Added bulk catalog promotion service at `services/food_bulk_catalog_service.py`.
- Added bulk promotion CLI at `scripts/promote_canonical_food_bulk_catalog.py`.
- Added focused tests for inventory, importer category enrichment, dry-run behavior, category filters, raw-safety rules, duplicate-name handling, idempotency, search aliases, and canonical logging.

## Inventory Tooling

The inventory report is read-only and includes:

- raw source row count by `source_name`
- raw source row count by `data_type`
- raw source row count by `food_category`
- macro coverage counts
- canonical food count
- canonical source link count
- optional FDC `food.csv` count by data type
- optional FDC Foundation count by readable category
- notes explaining when an FDC directory has Foundation rows but the active DB has no imported raw source rows

## Import Category Handling

FDC directory import remains defaulted to `foundation_food`.

When the directory contains `food_category.csv` and `food.csv` contains `food_category_id`, the importer stores readable categories such as:

- `Fruits and Fruit Juices`
- `Vegetables and Vegetable Products`
- `Dairy and Egg Products`
- `Finfish and Shellfish Products`

Older rows and fixtures without category ids remain compatible.

## Bulk Candidate Rules

Default candidate requirements:

- `source_name = USDA FoodData Central`
- `data_type = foundation_food`
- at least one macro value is present
- category is in the v0 allowed set
- source row is not review/test/acquisition-like
- raw meat, fowl, and fish are skipped unless clearly prepared/cooked/canned
- raw produce remains eligible
- existing primary source links are reported as `already_promoted`

Allowed v0 categories:

- `Vegetables and Vegetable Products`
- `Fruits and Fruit Juices`
- `Dairy and Egg Products`
- `Legumes and Legume Products`
- `Cereal Grains and Pasta`
- `Nut and Seed Products`
- `Fats and Oils`
- `Baked Products`
- `Soups, Sauces, and Gravies`
- `Spices and Herbs`
- `Sweets`
- `Beverages`
- `Poultry Products`
- `Beef Products`
- `Pork Products`
- `Finfish and Shellfish Products`
- `Sausages and Luncheon Meats`
- `Restaurant Foods`
- `Lamb, Veal, and Game Products`

## Raw Meat/Fowl/Fish Handling

For meat/fowl/fish categories, bulk promotion allows clearly prepared rows such as cooked, canned, roasted, grilled, broiled, braised, pan-broiled, pan-fried, restaurant, or drained entries.

Rows that are raw, uncooked, or not clearly prepared are reported as `skipped_unsafe_raw`.

The builder does not relabel raw meat/fowl/fish as cooked.

## Display Names and Aliases

Bulk promotion uses existing curation where possible and adds conservative known-pattern display names for common foods such as:

- `Grape tomatoes`
- `Hummus`
- `2% milk`
- `Egg`
- `Chicken breast`
- `Ground turkey`
- `Ground beef`
- `Tuna`
- `Olive oil`

Aliases include the original raw description, safe first phrase, and known common aliases when available.

## Idempotency and Duplicate Handling

- Dry-run does not mutate canonical tables.
- Non-dry-run promotes through the existing raw-source promotion service.
- Existing primary source links are reported as `already_promoted`.
- If a candidate display name already exists without a primary link for that source row, the row is reported as `skipped_duplicate_name`.
- If multiple unlinked source rows in one run curate to the same display name, all are reported as `skipped_duplicate_name`.
- This protects existing/manual canonical nutrient rows from accidental overwrite during broad catalog builds.

## CLI Usage

Inventory:

```powershell
.\.venv\Scripts\python.exe scripts/inspect_usda_food_catalog_sources.py --db-path fitness_ai.db --fdc-dir data --report-path tmp/source_inventory.json
```

Bulk dry-run:

```powershell
.\.venv\Scripts\python.exe scripts/promote_canonical_food_bulk_catalog.py --db-path fitness_ai.db --dry-run --report-path tmp/bulk_catalog_dry_run.json
```

Bulk promotion with cap:

```powershell
.\.venv\Scripts\python.exe scripts/promote_canonical_food_bulk_catalog.py --db-path fitness_ai.db --max-promotions 500 --report-path tmp/bulk_catalog_report.json
```

Optional filters:

- `--source-name`
- `--include-data-types`
- `--include-categories`
- `--exclude-categories`
- `--limit`
- `--max-promotions`
- `--report-path`

## Report Buckets

- `promoted`
- `already_promoted`
- `skipped_missing_macros`
- `skipped_unsafe_raw`
- `skipped_category`
- `skipped_duplicate_name`
- `skipped_ambiguous`
- `skipped_invalid`

## Expected Real-Data Target

The repo data snapshot contains hundreds, not tens of thousands, of relevant `foundation_food` rows. V0 is designed to produce a practical USDA-backed canonical catalog from those Foundation rows when they are imported into `raw_food_source_records`.

## Boundaries Preserved

- No frontend changes.
- No food logging UI changes.
- No serving picker, diary/history, admin curation UI, raw USDA review UI, AI parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration changes.
- No full FNDDS, SR Legacy, branded, sample, sub-sample, market acquisition, or agricultural acquisition expansion.
- No DB files, USDA datasets, ZIPs, generated reports, or tmp artifacts are part of this milestone.

## Deferred

- Manual curation UI.
- Serving-size and household-unit curation.
- Broader data-type expansion after Architecture approval.
- Fine-grained duplicate-resolution workflow.
- AI/parser-assisted food logging, barcode scanning, and image recognition.
