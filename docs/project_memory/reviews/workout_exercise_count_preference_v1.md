# Workout Exercise Count Preference v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: `WORKOUT_EXERCISE_COUNT_PREFERENCE_V1_ACCEPTED`

## Summary

Workout Exercise Count Preference v1 adds a deterministic workout size preference path so workouts can feel fuller without giving user preference unsafe authority over backend constraints.

The implementation adds Quick / Standard / Full choices in the Workout UI and threads the selected preference through preview and selection. The backend resolves the requested size into a safe final target count and appends only clean, catalog-backed, equipment-valid, non-duplicate accessory/core/conditioning work when the target count exceeds the base deterministic template.

## Count behavior

- Quick: target 4 exercises.
- Standard: target 5 exercises and default.
- Full: target 6 exercises.
- Maximum supported v1 count: 7.
- Recovery-limited scenario: clamps to 4.
- Data-quality-limited full request: clamps to 5.

## UI behavior

The Workout page now exposes `Workout size` before generation:

- Quick — 3 to 4 exercises
- Standard — 5 exercises
- Full — 6 to 7 exercises

User-safe helper copy states that recovery and equipment rules still apply.

After generation, the UI shows exercise count and a user-safe count reason such as:

- Built as a standard 5-exercise session.
- Built as a fuller 6-exercise session.
- Shortened to 4 exercises today to keep the session manageable.

## Intentional deferrals

- No persisted long-term workout size setting.
- No database migration.
- No 7-exercise default.
- No provider/AI exercise-count decisions.
- No workout programming redesign.
- No substitution algorithm changes.
- No performance optimization work.

Recommended future follow-up if useful: Workout Session Preference Persistence v1.

## Boundary confirmation

- No catalog changes.
- No provider calls added.
- No model promoted.
- No provider defaults changed.
- No AI-generated workout programming.
- No workout persistence lifecycle changes.
- No workout logging lifecycle changes.
- No database schema changes.
- No report persistence changes.
- No Daily Next Action changes.
- No Today Coach Note logic changes.
- No nutrition calculation changes.
- No food logging logic changes.
- No raw IDs/debug JSON added to normal UI.
- No paid tools, Aider, Codex, Headroom, Claude workflow, or `CLAUDE.md` added.
- `qa_artifacts` remain untracked/local-only.

## Recommended next step

Manual QA should confirm Quick / Standard / Full generation, 5+ exercise substitution compatibility, Active Workout and Review handling for 5+ exercises, and latency observation across workout tabs.
