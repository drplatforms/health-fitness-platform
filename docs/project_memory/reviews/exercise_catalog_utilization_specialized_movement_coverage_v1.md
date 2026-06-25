# Review Notes — Exercise Catalog Utilization / Specialized Movement Coverage v1

Status: stabilization revision implemented / pending validation and smoke.

The implementation broadens deterministic workout slot candidate pools by adding catalog-backed alternatives that match the existing template slot movement patterns and current equipment constraints.

Safety/order of operations:

1. template slot intent remains primary
2. movement pattern must match the slot
3. available/unavailable equipment must be respected
4. avoided movements remain excluded
5. data-quality-limited sessions remain simple
6. variety participates only after safety/template constraints pass
7. selected workouts remain immutable after selection

Validation targets:

- exercise catalog service tests
- workout plan service tests
- workout selection/persistence tests
- Streamlit workout selection tests
- Today workout de-dup tests
- workout daily state lifecycle tests
- Daily Narrative regression tests
- Weekly Summary regression tests
- project memory checks
- Linux pull/smoke
- browser smoke

Architecture review should confirm whether this is sufficient for:

`EXERCISE_CATALOG_UTILIZATION_SPECIALIZED_MOVEMENT_COVERAGE_V1_ACCEPTED`


## Stabilization revision

Architecture required a narrow stabilization revision before acceptance. The revision addressed two blockers:

- Quick / Standard / Full workout size behavior no longer collapses Quick to the base four-exercise template. Quick trims to three main exercises, Standard targets five, and Full targets six when constraints allow. Recovery-limited sessions may still shorten Standard/Full with user-safe explanation.
- Selected/active rendering now preserves the cached selected payload for the current Streamlit session when the current endpoint returns a competing persisted state, so preview variation cannot overwrite the just-selected visible workout during rerun. Backend API tests confirm preview variation does not mutate selected or active persisted exercises.

No provider/AI workout generation was introduced. Latency optimization remains deferred.
