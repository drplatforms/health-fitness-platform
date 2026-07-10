# Workout Set Logging UX v0.1

Current source of truth: `feature/workout-set-logging-ux-v0-1`.

Status:

```text
WORKOUT_SET_LOGGING_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make actual workout set logging faster and clearer while preserving the existing workout execution model and backend-owned logged-set truth.
```

Implemented scope:

- Added a backend actual-set delete path alongside the existing create/edit behavior.
- Added `DELETE /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}`.
- Kept actual-set delete scoped to the owning workout plan execution session and returned refreshed actual sets plus planned-vs-actual summary.
- Added frontend proxy support for actual-set PATCH and DELETE.
- Added frontend client helpers and response types for actual-set edit/delete.
- Updated the workout page to show saved set rows per planned exercise.
- Added inline saved-set edit controls for reps, weight, RIR, and notes.
- Added delete controls for mistaken actual-set rows.
- Added compact per-exercise logged-set count and no-sets-yet state.
- Kept previous-performance context read-only.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, recommendation behavior, nutrition, food logging, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Planned workout snapshots remain immutable.
- Actual set values remain user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_training_execution_summary_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/workout_plan_persistence_service.py api/routes/workout_plans.py tests/test_workout_plan_persistence_service.py`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint`
- `npm run build`
- `git diff --check`
