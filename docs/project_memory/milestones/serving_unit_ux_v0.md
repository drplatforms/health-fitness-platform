# Serving Unit UX v0

Branch: `feature/serving-unit-ux-v0`

Status: `SERVING_UNIT_UX_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Serving Unit UX v0 lets users log canonical foods by grams or by an approved serving unit. The backend remains the source of truth: serving-unit requests resolve to grams before persistence, and canonical nutrition snapshots continue to come from canonical nutrient rows.

## Implemented Scope

- Canonical food logging accepts exactly one amount mode:
  - grams mode: `canonical_food_id`, `grams`, optional `entry_date`, `meal_type`, and `notes`.
  - serving-unit mode: `canonical_food_id`, `serving_unit_id`, `quantity`, optional `entry_date`, `meal_type`, and `notes`.
- Serving-unit mode verifies active canonical food, active serving unit, and serving-unit ownership before resolving grams.
- Resolved grams are bounded by the same canonical logging guard as direct grams logging.
- Public serving-unit discovery includes frontend-friendly aliases (`id`, `display_label`, `grams_per_unit`, `is_default`) while preserving existing keys.
- The food logging card now fetches approved units for the selected canonical food, always offers grams, defaults to the first approved serving unit when present, previews resolved grams, and logs through the canonical endpoint.
- Starter serving-unit seeds now include reviewed aliases for raw chicken breast and 90/10 and 80/20 ground beef.

## Boundaries Preserved

- No real promotion, raw source promotion, barcode scanning, meal planning, provider/AI behavior, RAG, embeddings, vector search, or runtime agent orchestration was added.
- Serving units are manually curated app data; raw source payloads are not exposed in public serving-unit responses.
- Persisted nutrition truth remains `food_entries.canonical_food_id` plus resolved `grams`; serving-unit metadata is provenance only.
- Existing grams logging, canonical daily logs, daily nutrition actuals, and target-vs-actual behavior remain stable.

## Validation

Targeted backend validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_nutrition_serving_unit_data_model_v1.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_food_logging_api.py -q
```

Additional validation target:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_target_vs_actual_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_api_smoke.py -q
.\.venv\Scripts\python.exe -m ruff check services api tests scripts
cd frontend
npm run lint
npm run build
```
