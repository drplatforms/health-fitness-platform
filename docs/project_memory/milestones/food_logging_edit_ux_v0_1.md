# Food Logging Edit UX v0.1

Branch: `feature/food-logging-edit-ux-v0-1`

Status: `FOOD_LOGGING_EDIT_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Food Logging Edit UX v0.1 makes correction of logged canonical foods match the serving-aware logging flow. Users can edit an existing canonical food entry using grams or an approved serving unit, while the backend continues to persist resolved grams and canonical nutrient snapshots as the source of truth.

## Implemented Scope

- Extended `PATCH /nutrition/{user_id}/canonical-logs/{entry_id}` to accept either grams or `serving_unit_id` + `quantity`.
- Preserved meal-only edit support.
- Serving-unit edits validate active serving units, serving-unit ownership, active canonical foods, quantity, and resolved gram bounds.
- Serving-unit edits recalculate macro snapshots and create or update serving-unit metadata for the existing food entry.
- Grams edits clear stale serving metadata from entries previously logged or edited by serving unit.
- Delete removes serving metadata before deleting the owned canonical food entry.
- Daily canonical logs include optional serving fields when available: `serving_unit_id`, `serving_quantity`, `serving_display`, `resolved_grams`, `amount_source`, and `serving_unit_confidence`.
- Logged Today edit mode now supports grams fallback, serving-unit selector, previous serving prefill, resolved grams preview, and macro preview.

## Boundaries Preserved

- No favorites, meal templates, full diary/history, barcode scanner, AI parser, AI suggestions, meal planning, raw-source logging, target formula changes, Daily Coach changes, report changes, workout changes, provider changes, RAG, embeddings, vector search, or agent orchestration were added.
- Backend remains responsible for serving-unit resolution, macro snapshots, ownership checks, and canonical persistence.
- Frontend remains a compact renderer/controller and does not calculate authoritative nutrition.
- Raw USDA/source payloads are not exposed.

## Validation

Focused edit validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_log_edit_serving_units_api.py tests/test_canonical_food_log_edit_serving_units_service.py -q
```

Targeted nutrition/serving/recents regression:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_log_edit_serving_units_api.py tests/test_canonical_food_log_edit_serving_units_service.py tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_food_logging_recents_api.py tests/test_food_logging_recents_service.py tests/test_nutrition_target_vs_actual_service.py tests/test_api_smoke.py -q
```

Lint, format, and frontend validation:

```powershell
.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py services/nutrition_serving_unit_logging_service.py services/nutrition_serving_unit_service.py services/food_logging_recents_service.py tests
.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py services/nutrition_serving_unit_logging_service.py services/nutrition_serving_unit_service.py services/food_logging_recents_service.py tests/test_canonical_food_log_edit_serving_units_api.py tests/test_canonical_food_log_edit_serving_units_service.py
cd frontend
npm run lint
npm run build
```
