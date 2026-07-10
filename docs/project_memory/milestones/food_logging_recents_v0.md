# Food Logging Recents v0

Branch: `feature/food-logging-recents-v0`

Status: `FOOD_LOGGING_RECENTS_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Food Logging Recents v0 reduces repeated daily logging friction by deriving recent canonical foods from existing logs. Users can reselect a recently logged canonical food and reuse the last grams or approved serving-unit context before submitting through the existing canonical logging path.

## Implemented Scope

- Added `services/food_logging_recents_service.py`.
- Added `GET /nutrition/{user_id}/recent-canonical-foods?limit=10`.
- Recent results are user-scoped, bounded, active-canonical-only, distinct by `canonical_food_id`, and ordered by the latest log entry.
- Recent records include last grams, last logged date/time, last meal type, usage count, and available macro snapshots.
- Serving-unit recent records include the last serving unit ID, original serving display, and serving quantity when the latest entry has serving metadata.
- Grams-only recent records remain usable when no serving metadata exists.
- Added a frontend proxy route and API helper for recent canonical foods.
- Updated `FoodLoggingCard` with compact Recent Foods chips. Selecting a recent item prepopulates the selected canonical food, amount/unit, and meal while still allowing edits before logging.

## Boundaries Preserved

- No favorites, meal templates, full diary/history, barcode scanner, AI parser, AI suggestions, meal planning, raw-source logging, nutrition target changes, workout changes, provider changes, RAG, embeddings, vector search, or agent orchestration were added.
- Backend still owns serving-unit resolution, nutrient snapshots, and canonical logging persistence.
- Recent foods are derived from existing logs; no new recents table or preference persistence was introduced.
- Raw USDA/source payloads are not exposed.
- Missing nutrient values remain missing rather than being coerced to zero.

## Validation

Focused backend validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_target_vs_actual_service.py -q
```

Lint, format, and frontend validation:

```powershell
.\.venv\Scripts\python.exe -m ruff check services api tests scripts
.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/food_logging_recents_service.py tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py
cd frontend
npm run lint
npm run build
```
