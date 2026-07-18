# Validation Matrix

This matrix maps common Fitness AI areas to maintainable targeted validation. Targeted, risk-based validation is the default: use the narrowest credible checks for the actual change and expand only when the blast radius justifies it.

Full `pytest -q` is not a default milestone or closeout requirement. It may run only when Architecture explicitly authorizes it and records a concrete cross-cutting risk justification. Milestone closeout by itself is never sufficient justification. When a broad or full suite is useful but Codex does not need to reason through its execution, prefer running it outside the expensive Codex implementation session where practical.

Run Python commands from the repository root with the project virtual environment.

## Validation Escalation Policy

- **Mechanical data/content expansion:** focused affected-feature tests plus only relevant static, build, integrity, or smoke checks.
- **Frontend-only change:** affected frontend tests, lint/build, and required production browser smoke.
- **Bounded backend change:** affected service/API tests plus the nearest credible regression slices.
- **Shared contract or cross-cutting behavior:** broaden to the relevant category-level suites.
- **Full repository suite:** exceptional; requires explicit Architecture authorization and a recorded concrete cross-cutting risk justification.

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

Do not run full `pytest -q` unless Architecture explicitly authorizes it and records the concrete cross-cutting risk that makes targeted validation insufficient.

Potential justifications include foundational persistence/database infrastructure changes, global test-fixture or test-infrastructure changes, central shared contracts with broad blast radius, major architecture migrations, or targeted validation that exposes an unexplained wider regression.

Milestone completion or closeout alone is never justification for a full-suite run. Silence in a handoff means targeted validation only.
