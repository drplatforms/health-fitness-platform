# Exercise History & Progress Analytics v1

Branch: `feature/exercise-history-progress-analytics-v1`

Baseline: `main` at `80f7209`

Status:

```text
EXERCISE_HISTORY_PROGRESS_ANALYTICS_V1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Objective

Add a dedicated retrospective Workout History surface that answers what the user
has trained, how often, what was logged recently, and how comparable recent
working loads differ without making physiological-progress claims.

## Implemented behavior

- Added bounded read-only
  `GET /workout-plans/{user_id}/exercise-history-analytics` with explicit
  lookback, exercise, and recent-session limits.
- Overall history reports completed planned workouts, completed non-skipped
  sets, distinct effective exercises, and the most recent completion date.
- Exercise summaries are ordered by most recent performance and include stable
  effective identity, completed-session count, deterministic latest-session
  summary, existing recent-best-set semantics, logging quality, one concise
  limitation, a bounded recent-session series, and conservative comparable-load
  trend facts.
- A catalog-backed effective group retains its unique non-null catalog identity
  even when its most recent name-alias session is untagged.
- Substitution identity reuses the existing progression-history evidence loader.
  Catalog identity takes precedence, with normalized effective-name fallback and
  alias merging when one name maps unambiguously to one catalog exercise.
- Comparable session weight reuses the progression engine's complete prescribed
  working-set and consistent-positive-weight standard.
- Trend status is limited to `higher_recently`, `steady`, `lower_recently`, and
  `insufficient_data`; the UI omits insufficient trends and uses neutral wording.
- Added `/workout/history` under the existing Workout product area with
  `Today | Week | History`, a compact searchable selector, local exercise
  switching, concise recent-session rows, one empty state, and one incomplete
  logging note.
- `/workout/history` remains highlighted as Workout in primary mobile
  navigation and preserves the existing Workout theme on mobile and desktop.

## Boundaries preserved

- No schema migration, analytics persistence, workout mutation, adaptive
  progression change, legacy/manual log unification, provider, AI, RAG,
  embedding, prediction, chart dependency, or cross-domain analysis was added.
- The public progression-history and progression-decision behaviors remain
  unchanged.
- `WorkoutPreviewExperience.tsx` was not modified. Existing behavior still hides
  no-history Previous Performance, insufficient-data Next Target, and empty
  intelligence wrappers while preserving meaningful intelligence.
- Public analytics exclude raw rows, notes, planned workout JSON, internal
  reason codes, and internal plan/session/planned-exercise IDs.

## Implementation validation

- New analytics service/API tests: 13 passed, including the reverse
  catalog-backed-to-newer-untagged alias regression.
- Combined analytics, progression history/decision, workout persistence, and
  execution-summary regression slice: 145 passed.
- Direct substitution service/persistence/UX regression slice: 49 passed.
- Focused frontend navigation/identity/trend helper tests: 6 passed.
- Touched-file Ruff lint and format checks: passed.
- Frontend lint: passed with no warnings.
- Frontend production build: passed and includes `/workout/history` plus
  `/api/workout-exercise-history-analytics`.
- Isolated production browser smoke used a physical disposable database copy
  with the official longitudinal QA seed and a backend launcher that explicitly
  patched `database.DB_PATH` before importing the app.
- Browser smoke passed for user 102 data, exercise search/switching, user switch
  reset, one empty state, Today/Week/History navigation, Workout mobile-nav
  highlighting, active-workout placeholder cleanup, 390px and desktop layouts,
  Light/Dark themes, horizontal overflow, and console errors.
- All scoped smoke processes and temporary files were removed.

Canonical `fitness_ai.db` was not an automated test or smoke target. A session-
wide hash change was confirmed by the user to be concurrent live-app activity;
no canonical data was inspected, reversed, or modified in response.

Architecture retains source review, acceptance smoke, acceptance-state memory,
and all staging, commit, push, merge, merged-main validation, and snapshot
authority.
