# Workout Progression History v0

Current source of truth: `feature/workout-progression-history-v0`.

Status:

```text
WORKOUT_PROGRESSION_HISTORY_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add compact previous-performance context to the workout flow so planned exercises can show what the user did last time for the same exercise.
```

Implemented scope:

- Added a read-only workout progression history service for completed planned workout executions.
- Added `POST /workout-plans/{user_id}/progression-history` for bounded, user-scoped exercise history summaries.
- Summaries include no-history state, completed session count, last performed date, compact last-session summary, recent best set, logging-quality classification, and safe messages.
- Kept public API output bounded and excluded raw actual-set rows and notes.
- Added workout detail UI previous-performance lines near each exercise.
- Added a frontend proxy route and typed client helper for workout progression history.

Boundaries preserved:

- No automatic progression engine, load increase, deload, periodization, workout generation, recommendation, nutrition, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Existing workout preview, select, start, actual-set logging/editing, completion, history, and planned-vs-actual response shapes remain additive/stable.
- Only completed planned workout executions are used for user-facing history.
- Incomplete logging produces limited-state messaging instead of coaching claims.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- Existing workout regression slice with available test files.
- Existing recommendation stability slice with available test files.
- `.\.venv\Scripts\python.exe -m ruff check services api tests scripts`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint`
- `npm run build`
- `git diff --check`
