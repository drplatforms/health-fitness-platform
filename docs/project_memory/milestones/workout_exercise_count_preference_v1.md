# Workout Exercise Count Preference v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Goal

Move generated workouts away from a hard fixed 4-exercise feel by adding a bounded workout size preference while keeping backend safety constraints in control.

## Implemented behavior

Workout size choices:

- Quick: targets 4 exercises.
- Standard: targets 5 exercises and is the default.
- Full: targets 6 exercises, with v1 backend maximum support capped at 7.

Backend count resolution:

- Normal/default sessions target 5 exercises.
- Full sessions target 6 exercises where the deterministic candidate set supports it.
- Recovery-limited sessions clamp to 4 exercises.
- Data-quality-limited full requests clamp to 5 exercises.
- Final count never exceeds 7.
- User preference is an input, not an override.

## Scope boundaries

This milestone does not change provider/model behavior, persistence/schema, reports, Daily Coach logic, nutrition calculations, food logging, catalog data, or AI-generated workout programming.

The deterministic generator is extended only enough to honor a safe target count by adding clean, equipment-valid, non-duplicate accessory/core/conditioning slots. It does not redesign exercise scoring/ranking, workout lifecycle, logging lifecycle, or substitution backend behavior.

## Files

- `services/workout_exercise_count_service.py`
- `services/workout_plan_service.py`
- `services/workout_plan_persistence_service.py`
- `models/workout_plan_models.py`
- `api/routes/workout_plans.py`
- `ui/streamlit_app.py`
- `tests/test_workout_exercise_count_preference_v1.py`
- `tests/test_workout_plan_service.py`
- `tests/test_exercise_catalog_service.py`
- `docs/project_memory/reviews/workout_exercise_count_preference_v1.md`

## Validation focus

- Quick / Standard / Full count resolution.
- Recovery and data-quality clamping.
- Standard 5-exercise generation.
- Full 6-exercise generation where candidates allow.
- Unique exercises and equipment-compatible additions.
- Preview/select routes preserve preference.
- Active workout state handles 5+ exercises.
- Existing substitution UX remains compatible.
