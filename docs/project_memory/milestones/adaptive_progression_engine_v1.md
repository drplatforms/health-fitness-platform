# Adaptive Progression Engine v1

Branch: `feature/adaptive-progression-engine-v1`

Baseline: `main` at `edd32f8`

Status:

```text
ADAPTIVE_PROGRESSION_ENGINE_V1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Objective

Add one deterministic, explainable, advisory progression decision for each
effective exercise in an actionable current workout so the product can answer:

```text
What should I try to beat today, and why?
```

## Implemented behavior

- Added a bounded read-only progression decision service with exactly these
  outcomes: `progress_reps`, `increase_load`, `hold`, `ease_back`, and
  `insufficient_data`.
- Uses only completed planned-workout executions and the historical rep/RIR
  prescription copied onto each actual set when it was performed.
- Requires the latest matching completed session to contain complete evidence
  for every required historical working set; newer incomplete evidence is never
  skipped in favor of older positive evidence.
- Ignores extra sets beyond the historical planned set count when determining
  progression eligibility.
- Requires two consecutive top-range qualifying sessions before recommending
  the next practical load or resistance; no numeric next load is invented.
- Requires two consecutive conservative meaningful-underperformance sessions
  before recommending `ease_back`; one difficult session produces `hold`.
- Uses a consistent positive latest-session weight only as an optional reference.
  Missing, zero-only, or varied weight produces non-numeric guidance.
- Reuses Recovery Intelligence v2 exactly once per API request. Only
  `readiness_classification == recovery_limited` or
  `fatigue_support == limiting` brakes an otherwise upward decision to `hold`.
- Makes historical evidence substitution-aware through replacement catalog
  identity with normalized effective-name fallback while preserving the current
  immutable planned slot's sets, reps, and RIR prescription.
- Added `POST /workout-plans/{user_id}/progression-decisions` with a structured
  current-exercise request and bounded response. The endpoint performs no write.
- Added a typed Next.js proxy/client contract and a compact `NEXT TARGET` block
  beside Previous Performance in preview and active current-workout states.
- Applying a substitution refreshes both Previous Performance and Next Target
  for the replacement effective exercise.
- Completed and historical read-only workout states do not display actionable
  Next Target coaching.

## Boundaries preserved

- Advisory only: no ApprovedWorkoutPlan, planned exercise, actual-set default,
  substitution ranking, workout generation, recovery classification, or user
  data is mutated.
- No schema migration or progression-decision persistence was added.
- No invented equipment increments, periodization, deload automation, volume
  planning, provider, AI, RAG, embedding, or agent scope was added.
- Public Workout Progression History response shape remains unchanged.
- Automated validation uses isolated temporary databases; the canonical
  `fitness_ai.db` is not an automated test target.

## Implementation files

- `services/workout_progression_decision_service.py`
- `services/workout_progression_history_service.py`
- `api/routes/workout_plans.py`
- `frontend/src/app/api/workout-progression-decisions/route.ts`
- `frontend/src/components/WorkoutPreviewExperience.tsx`
- `frontend/src/lib/todayWorkoutApi.ts`
- `frontend/src/types/todayWorkout.ts`
- `tests/test_workout_progression_decision_service.py`
- `tests/test_workout_progression_decision_api.py`

## Implementation validation

- New progression service/API tests: 16 passed.
- Existing progression-history service/API regression: 12 passed.
- Recovery Intelligence v2 service regression: 10 passed.
- Substitution persistence/application, workout persistence/actual-set,
  planned-vs-actual/completion, and daily lifecycle regression: 145 passed.
- Touched-file Ruff check: passed.
- Frontend lint: passed.
- Frontend production build: passed and included the new proxy route.

Production-mode implementation smoke and final repository safety evidence are
recorded in the Architecture completion report rather than treated as acceptance.
Architecture retains final acceptance-state and Git closeout ownership.
