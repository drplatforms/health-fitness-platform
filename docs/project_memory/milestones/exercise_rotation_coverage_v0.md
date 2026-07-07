# Exercise Rotation Coverage v0

Branch: `feature/exercise-rotation-coverage-v0`

Source baseline: `main` at `5d52e03 Merge canonical food bulk catalog hardening v0.1`.

Requested status:

```text
EXERCISE_ROTATION_COVERAGE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Purpose

Increase deterministic workout exercise coverage so preview rotation can use most of the curated, equipment-compatible, generator-eligible exercise catalog over time without changing provider behavior, workout size rules, persistence, or frontend surfaces.

## Implemented Scope

- Added `services/workout_rotation_pool_service.py` as a narrow catalog-driven slot pool builder.
- Expanded anchored deterministic lower, push, pull, accessory, and additional Standard/Full slots with catalog candidates after the existing safe anchors.
- Preserved anchor order so existing deterministic defaults remain priority anchors while broader catalog entries become reachable through preview variation.
- Added slot-family filters for lower primary, push primary, pull primary, core, carry, arms/accessory, shoulder/upper-back, and conditioning finish work.
- Excluded mobility entries from generator pools and kept rotator-cuff-style internal/external rotation drills out of primary pull slots.
- Preserved equipment constraints, unavailable equipment exclusion, preview variation rotation, recent-exercise penalties, duplicate-name protection, and same-workout rotation-group protection.
- Tightened deterministic selection so avoid movements and movement restrictions apply to hard-coded anchors as well as catalog-expanded options.
- Extended the utilization diagnostic to report generator-eligible counts, full candidate names, selected exercise types, not-selected reasons, and slot-family pool sizes.
- Added `tests/test_exercise_rotation_coverage_v0.py` and updated existing coverage expectations for the broader catalog behavior.

## Diagnostic Result

Read-only diagnostic command:

```powershell
.\.venv\Scripts\python.exe tools/exercise_catalog_utilization_diagnostic.py --variation-count 25
```

Final local result:

```text
total_active_exercises: 240
total_equipment_eligible_exercises: 237
total_generator_eligible_exercises: 224
total_unique_selected_exercises: 126
total_equipment_eligible_never_selected: 111
total_equipment_eligible_not_in_candidate_options: 18
total_generator_eligible_not_selected: 98
total_specialized_never_selected: 30
```

Coverage improved materially from the pre-change 25-variation local diagnostic result of 69 selected exercises, and from the earlier documented narrow-sweep baseline of about 54 selected exercises.

Selected movement-pattern coverage includes:

```text
horizontal_pull, vertical_push, horizontal_push, core_anti_extension,
hinge, vertical_pull, arms_biceps, squat, core_anti_rotation, lunge,
arms_triceps, carry, conditioning
```

The `>=120` target was achieved with 126 unique selected exercises. Mobility remained unselected as an exercise type.

## Boundaries Preserved

- No provider, OpenAI, Ollama, CrewAI, RAG, embedding, vector, agent, frontend, database schema, food catalog, serving/nutrition, clinical/rehab, periodization, progression, or 1RM changes were added.
- No exercise catalog entries were added.
- No selected-workout persistence behavior was intentionally changed.
- No DB files, generated reports, snapshots, ZIPs, or temporary artifacts are part of this milestone.

## Deferred

- Mobility-specific warmup/cooldown slot modeling remains deferred.
- More nuanced rotation-group families for similar curls, rows, carries, and presses remain a future refinement if same-session duplication ever becomes too restrictive or too loose.
- Advanced/high-skill selection can be further tuned with richer catalog metadata in a later milestone.

## Validation

Required local validation target:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_exercise_rotation_coverage_v0.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_exercise_catalog_service.py tests/test_exercise_eligibility_matrix_v1.py tests/test_exercise_catalog_utilization_specialized_movement_coverage_v1.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py -q
.\.venv\Scripts\python.exe -m ruff check services tools tests
.\.venv\Scripts\python.exe -m ruff format --check services tools tests
git diff --check
```
