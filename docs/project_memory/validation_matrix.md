# Validation Matrix

This matrix maps common Fitness AI areas to maintainable targeted validation. It is guidance, not a ceiling: milestone-specific risk, cross-module contracts, or newly discovered regressions may require additional tests. Full `pytest -q` is not the default because it is slow.

Run Python commands from the repository root with the project virtual environment.

## Workout Persistence And Actual-Set Logging

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py -q
```

## Workout Generation And Selection

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py -q
```

## Today Workout Routes And Views

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_today_workout_view_models.py -q
```

## Workout Progression History

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q
```

## Canonical Food Logging

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py -q
```

## Serving-Unit Behavior

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_nutrition_serving_unit_data_model_v1.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_food_logging_api.py -q
```

## Food Recents And Edit Flows

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py tests/test_canonical_food_log_edit_serving_units_service.py tests/test_canonical_food_log_edit_serving_units_api.py -q
```

## Frontend Lint And Build

Run from `frontend/`:

```powershell
npm run lint
npm run build
```

Lint and build do not replace browser smoke for UI-impacting work.

## Production Browser Smoke

Use a production frontend build and a backend pointed at a temporary copy of `fitness_ai.db` or another explicitly safe test database. Confirm the scoped workflow, persisted-state refresh, console errors, accessibility names and keyboard behavior, and horizontal overflow around a 390px viewport. Remove the temporary database, launchers, logs, and reports after testing.

## Project-Memory Checks

```powershell
.\.venv\Scripts\python.exe tools/project_memory_check.py --project-root .
.\.venv\Scripts\python.exe -m pytest tests/test_project_memory_check.py -q
```

## Full Suite Conditions

Run full `pytest -q` only when the milestone changes broad shared contracts, migrations, cross-domain state, provider or fallback behavior, test infrastructure, or when targeted checks reveal wider regressions. Architecture or QA may also require it for acceptance.
