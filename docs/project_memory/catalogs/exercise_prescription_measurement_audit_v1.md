# Exercise Prescription Measurement Semantics Audit v1

Status: evidence and architecture recommendation only. No runtime catalog, canonical ID, taxonomy, generation, persistence, execution logging, progression, API, database, or frontend behavior changed.

Baseline: `main @ 8751e54` (`Merge exercise families and structured variants v1`).

Audit branch: `feature/exercise-prescription-measurement-audit-v1`.

Companion evidence: `docs/project_memory/catalogs/exercise_prescription_measurement_matrix_v1.csv`.

## 1. Executive summary

**Repository fact:** the repository-owned catalog contains exactly 240 canonical exercise names. The accepted taxonomy matrix contains exactly those same 240 names.

**Audit classification:** every identity received an explicit exercise-level review. Default modes are 203 `reps`, 29 `duration`, and 8 `distance`. Thirty-one exercises have more than one intentionally allowed mode. Primary dispositions are 205 `MEASUREMENT_CLEAR`, 19 `MULTI_MODE_VALID`, 0 `MEASUREMENT_REVIEW_REQUIRED`, and 16 `PROTOCOL_IDENTITY_CANDIDATE`.

**Architecture recommendation:** implementation v1 should support exactly three singular planned-exercise measurement types:

```text
reps
duration
distance
```

Each planned exercise selects one primary `measurement_type`. Catalog metadata separately provides a reviewed default and bounded allowed modes. `duration_distance` should not be a fourth type because it confuses simultaneous targets with valid alternatives.

Use exact scalar `target_duration_seconds` and `target_distance_meters` fields in v1. Preserve rep ranges. Keep `sets` for all modes, where a set means one work block. Keep weight/load independent and optional at the plan/actual boundary. Make RIR nullable and type-aware; do not require it for duration- or distance-mode work.

**Uncertainty:** the audit found no identity whose measurement mode itself requires review. Architecture still needs to approve the three-mode contract, multi-mode list, scalar target choice, distance unit, and legacy non-null-column migration strategy.

## 2. Baseline, evidence, and method

**Repository fact:** `services/exercise_catalog_service.py` owns `CURATED_EXERCISE_CATALOG`. Static source extraction found 240 names and 240 unique names without importing or opening the database. The accepted taxonomy matrix has 240 unique rows, no missing catalog name, and no unknown name.

**Audit method:** accepted taxonomy family, base movement, physical variants, protocol, and notes were reviewed in six bounded 40-row groups. A temporary local tool only extracted, joined, counted, rendered, and validated reviewed data. It did not assign semantics by token or rule. The final choice for every row was explicitly authored.

Repository source entries do not carry stable persisted catalog IDs before seeding, so `catalog_exercise_id_if_resolvable` is blank as authorized. Exact canonical-name coverage is authoritative for this audit.

Labels used below:

- **Repository fact:** observed current code, schema, or accepted evidence.
- **Audit classification:** reviewed exercise-level result.
- **Architecture recommendation:** proposed future design, not accepted runtime behavior.
- **Uncertainty:** requires Architecture judgment or later evidence.

No database, provider, external API, or name-token classifier was used.

## 3. Definitions and notation

**Physical identity** is what is performed. **Family** and **base movement** come from accepted taxonomy evidence. **Measurement mode** is the primary unit used to prescribe/log a work block. **Protocol** describes organization such as intervals, tempo, pause, recovery, or cadence.

`default_measurement_mode` is the preferred default. `allowed_measurement_modes` is a bounded set of alternatives, using stable notation:

```text
reps
duration
distance
reps|duration
reps|distance
duration|distance
```

A pipe means “select one,” not “target every dimension simultaneously.”

- `reps` uses a positive minimum/maximum range.
- `duration` uses one positive integer target in seconds for v1.
- `distance` uses one positive numeric target in canonical meters for v1.
- Secondary observations are future data and not required in v1.
- `sets_applicable=yes` means the exercise can be one or more work blocks.

Load applicability:

- `applicable`: external load/resistance is inherent and meaningful.
- `optional`: the identity is valid unloaded, but added load is meaningful.
- `not_applicable`: external load is not a useful normal target/actual.
- `ambiguous`: reserved for unresolved evidence; no row required it.

RIR applicability:

- `applicable`: repetition capacity is a meaningful effort model.
- `not_applicable`: rep-in-reserve does not fit the modality.
- `ambiguous`: mode-dependent or too technique-dependent to require universally.

Dispositions:

- `MEASUREMENT_CLEAR`: one mode is sufficient.
- `MULTI_MODE_VALID`: multiple modes are intentionally valid.
- `MEASUREMENT_REVIEW_REQUIRED`: evidence cannot support a responsible choice.
- `PROTOCOL_IDENTITY_CANDIDATE`: the identity embeds protocol semantics but still has a compatibility measurement.

## 4. Classification counts

### Default measurement modes

| Default mode | Exercises |
| --- | ---: |
| reps | 203 |
| duration | 29 |
| distance | 8 |
| **Total** | **240** |

### Primary dispositions

| Disposition | Exercises |
| --- | ---: |
| MEASUREMENT_CLEAR | 205 |
| MULTI_MODE_VALID | 19 |
| MEASUREMENT_REVIEW_REQUIRED | 0 |
| PROTOCOL_IDENTITY_CANDIDATE | 16 |
| **Total** | **240** |

Thirty-one rows have multiple allowed modes. Twelve are protocol candidates and therefore retain `PROTOCOL_IDENTITY_CANDIDATE`; the other 19 use `MULTI_MODE_VALID`.

### Applicability and confidence

| Dimension | Value | Exercises |
| --- | --- | ---: |
| Sets | yes | 240 |
| Load | applicable | 164 |
| Load | optional | 34 |
| Load | not_applicable | 42 |
| RIR | applicable | 171 |
| RIR | ambiguous | 18 |
| RIR | not_applicable | 51 |
| Confidence | high | 210 |
| Confidence | medium | 30 |

No row has low measurement confidence. Medium confidence records bounded choice or protocol-boundary judgment, not an unresolved default.

## 5. Multi-mode candidates

| Group | Exercises | Default and alternatives |
| --- | --- | --- |
| Loaded carries | Farmer Carry; Suitcase Carry; Waiter Carry; Dumbbell Front Rack Carry; Plate Pinch Carry | distance default; `duration|distance` allowed |
| Loaded marches | Dumbbell Farmer March; Dumbbell Suitcase March | reps default; `reps|duration` allowed |
| Treadmill | Treadmill Walk; Treadmill Incline Walk; Treadmill Intervals; Treadmill Easy Jog; Treadmill Hill Intervals; Treadmill Tempo Run; Treadmill Recovery Walk; Treadmill Easy Intervals | duration default; `duration|distance` allowed |
| Stationary bike | Bike Steady State; Bike Intervals; Bike Recovery Ride; Bike Tempo Ride; Bike Hill Intervals; Bike Easy Spin | duration default; `duration|distance` allowed |
| Ground/core conditioning | Mountain Climber; Hollow Rock; Stability Ball Stir-the-Pot; Plank Shoulder Tap | duration or reps default as recorded; `reps|duration` allowed |
| Locomotion/gait | Bear Crawl; Toe Walk; Heel Walk | distance default; `duration|distance` allowed |
| Dynamic steps | Walking Lunge; Band Lateral Walk; Band Monster Walk | reps default; `reps|distance` allowed |

`Bike Cadence Drill` intentionally allows duration only. Cadence remains a deferred protocol detail, not a new target type.

## 6. Review-required findings

**Audit classification:** no identity requires `MEASUREMENT_REVIEW_REQUIRED`.

Taxonomy-review and alias candidates do not create measurement ambiguity:

- Barbell Squat remains rep-based regardless of unresolved bar position.
- Standing Calf Raise and Dumbbell Calf Raise remain rep-based despite pattern review.
- Cable Kickback is rep-based whether future ownership confirms glute or triceps meaning.
- Chest-Supported Row, Cable Lat Pulldown, and Dead Hang retain their possible aliases’ measurement modes.

This does not resolve or supersede their taxonomy questions.

## 7. Measurement-model recommendation

Every planned exercise should have exactly one `measurement_type`: `reps`, `duration`, or `distance`. The selected type must be allowed by canonical metadata. A generator uses the default unless an accepted protocol/template deliberately selects another allowed mode.

Do not add `duration_distance`. It is ambiguous between simultaneous targets, a primary target plus observation, and interchangeable alternatives. Optional secondary observations may be added later without changing the primary type.

Keep current rep ranges. Use exact scalar duration/distance targets in v1:

```text
target_duration_seconds: integer > 0
target_distance_meters: number > 0
```

This is the smallest useful contract. Duration/distance ranges, pace zones, and interval segments belong to later protocol work.

- Keep `sets >= 1` for all modes.
- Weight/load remains optional at the contract boundary; catalog applicability guides presentation.
- RIR fields are nullable and pair-valid when present.
- Duration and distance rows have null RIR in v1.
- `ambiguous` RIR rows are not forced to provide it.

## 8. Distance-unit recommendation

**Architecture recommendation:** store distance canonically in meters using `target_distance_meters` and `actual_distance_meters`.

Meters support short carries/crawls and long treadmill/bike work, avoid locale-dependent persistence, and permit deterministic UI conversion to feet, yards, kilometers, or miles. Twenty-five rows allow distance and explicitly recommend meters.

Stationary-bike distance is device-reported and should not be assumed comparable across devices. That limitation affects analytics, not storage.

## 9. Sets applicability

**Audit classification:** `sets` applies to all 240 identities. Its definition broadens from “sets of reps” to “work blocks”:

- strength: `3 sets × 8–10 reps`;
- plank: `3 sets × 30 seconds`;
- carry: `3 sets × 40 meters`;
- treadmill: `1 set × 1,800 seconds`.

Interval segment structure remains deferred to protocol templates. No removal of `sets` is recommended.

## 10. Load applicability

Load is applicable for 164 identities, optional for 34, and not applicable for 42. It remains independent of mode:

- Farmer Carry: distance/duration plus applicable load.
- Plank: duration plus optional load.
- Band Anti-Rotation Hold: duration plus applicable resistance.
- Treadmill and stationary bike: no external weight field by default.

**Uncertainty:** `actual_weight` does not fully represent band resistance, machine settings, bodyweight, or device resistance. This audit does not redesign load; v1 should preserve it as optional and avoid claiming universal coverage.

## 11. RIR applicability

RIR is applicable for 171 identities, ambiguous for 18, and not applicable for 51. It remains appropriate for conventional rep-based strength/hypertrophy work, but not universally for:

- holds;
- carries and distance locomotion;
- treadmill or bike work;
- mobility;
- timed conditioning/control drills.

Ambiguous cases include walking lunges with a distance option, marches with a duration option, Pallof presses, external rotations, and eccentric/scapular pull-up drills. V1 should not require RIR for them.

## 12. Strength and isometric deep dive

**Repository fact:** current generation assigns positive rep and RIR ranges to every exercise, including holds and conditioning identities.

Conventional dynamic presses, pulls, squats, hinges, lunges, curls, extensions, raises, and loaded trunk flexion remain rep-based.

| Static identity | Default | Load | RIR |
| --- | --- | --- | --- |
| Plank | duration | optional | not_applicable |
| Side Plank | duration | optional | not_applicable |
| Wall Sit | duration | optional | not_applicable |
| Hollow Body Hold | duration | not_applicable | not_applicable |
| Superman Hold | duration | not_applicable | not_applicable |
| Dead Hang | duration | optional | not_applicable |
| Pull-Up Bar Dead Hang | duration | optional | not_applicable |
| Pull-Up Flexed-Arm Hang | duration | optional | not_applicable |
| Stability Ball Plank | duration | optional | not_applicable |
| Band Anti-Rotation Hold | duration | applicable | not_applicable |
| Cable Anti-Rotation Hold | duration | applicable | not_applicable |

Duration measures the work block; it does not encode per-repetition tempo.

## 13. Carry deep dive

Farmer Carry, Suitcase Carry, Waiter Carry, Dumbbell Front Rack Carry, and Plate Pinch Carry are distance-first with duration allowed. Load remains applicable, sets remain meaningful, and RIR is not recommended.

Dumbbell Farmer March and Dumbbell Suitcase March differ intentionally: they are commonly in-place alternating cycles, so reps/steps are default and duration is allowed. Distance is not an allowed v1 target for march identities.

## 14. Treadmill deep dive

All eight treadmill identities default to duration and allow duration or distance. Load and RIR are not applicable.

`walk`, `jog`, and `run` are locomotion modes, not measurements. Incline is setup. Easy, recovery, tempo, intervals, and hill intervals are protocol. Interval identities preserve accepted uncertainty about walk/jog/run without blocking their duration/distance classification.

V1 does not add pace, speed, incline percentage, heart rate, calories, or interval-segment fields.

## 15. Stationary-bike deep dive

Stationary-bike work defaults to duration. Bike Steady State, Intervals, Recovery Ride, Tempo Ride, Hill Intervals, and Easy Spin also allow distance. Bike Cadence Drill allows duration only.

All seven bike identities are protocol candidates over one physical base. Watts, heart rate, calories, cadence targets, resistance levels, and cross-device distance normalization are deferred. Device capability does not create an implementation-v1 measurement type.

## 16. Mobility deep dive

Dynamic mobility is not automatically duration-based:

| Identity | Default | Reason |
| --- | --- | --- |
| Cat-Cow | reps | count flexion-extension cycles |
| Quadruped T-Spine Rotation | reps | count deliberate rotations |
| 90/90 Hip Switch | reps | count side-to-side switches |
| Band Shoulder Dislocate | reps | count complete passes |
| Wall Slide | reps | count controlled slide cycles |
| Prone Y-T-W Raise | reps | count controlled movement cycles |

Static Half-Kneeling Hip Flexor Stretch and Child's Pose Lat Stretch are duration-based. RIR is not a default for these mobility identities.

## 17. Dynamic conditioning and locomotion deep dive

| Identity | Default | Allowed | Rationale |
| --- | --- | --- | --- |
| Mountain Climber | duration | reps or duration | timed conditioning or counted contacts |
| Bear Crawl | distance | duration or distance | distance-first locomotion; time supports limited space |
| Toe Walk | distance | duration or distance | route length or time |
| Heel Walk | distance | duration or distance | route length or time |
| Band Lateral Walk | reps | reps or distance | counted steps or route length |
| Band Monster Walk | reps | reps or distance | counted steps or route length |
| Walking Lunge | reps | reps or distance | strength use counts reps; locomotion use may target distance |
| Hollow Rock | reps | reps or duration | cycles are primary; timed work is valid |
| Stability Ball Stir-the-Pot | reps | reps or duration | circles are primary; timed brace is valid |
| Plank Shoulder Tap | reps | reps or duration | contacts are primary; timed work is valid |

## 18. Protocol-candidate measurement analysis

The accepted taxonomy identified 16 protocol candidates. Every identity is preserved while physical measurement stays separate:

| Canonical identity | Default | Allowed | Protocol distinction |
| --- | --- | --- | --- |
| Treadmill Intervals | duration | duration or distance | intervals; locomotion unspecified |
| Bike Steady State | duration | duration or distance | steady_state |
| Bike Intervals | duration | duration or distance | intervals |
| Tempo Push-Up | reps | reps | tempo |
| Pause Squat | reps | reps | pause |
| Treadmill Easy Jog | duration | duration or distance | easy; jog locomotion |
| Treadmill Hill Intervals | duration | duration or distance | hill_intervals; locomotion unspecified |
| Treadmill Tempo Run | duration | duration or distance | tempo; run locomotion |
| Bike Recovery Ride | duration | duration or distance | recovery |
| Bike Tempo Ride | duration | duration or distance | tempo |
| Bike Hill Intervals | duration | duration or distance | hill_intervals/resistance protocol |
| Dumbbell Tempo Goblet Squat | reps | reps | tempo |
| Treadmill Recovery Walk | duration | duration or distance | recovery; walk locomotion |
| Treadmill Easy Intervals | duration | duration or distance | easy_intervals; locomotion unspecified |
| Bike Easy Spin | duration | duration or distance | easy |
| Bike Cadence Drill | duration | duration | cadence_drill; cadence target deferred |

The later Exercise Protocol Templates milestone owns protocol normalization.

## 19. Current rep-centric dependency map

| Layer | Repository fact | Future impact |
| --- | --- | --- |
| `models/workout_plan_models.py` | candidate, approved, planned, progression, and actual dataclasses embed reps/RIR | add singular type and nullable type-specific fields |
| workout provider contract | exact exercise keys require sets, reps, and RIR | add type plus nullable target dimensions |
| workout candidate parser | parses reps/RIR as required integers | parse by selected type |
| deterministic generation | assigns rep/RIR ranges to all selections, including Farmer Carry and Bike Steady State | choose catalog default and correct target dimension |
| candidate validator | rejects rep minimum below 1 and validates RIR universally | type-aware exclusive-target validation |
| workout renderer | always renders `sets × reps, RIR` | type-specific rendering |
| planned schema | `reps_min`, `reps_max`, `rir_min`, `rir_max` are non-null | explicit legacy compatibility rule |
| approved JSON reader | assumes all rep/RIR keys | missing type defaults to legacy reps |
| actual schema/model | only planned reps/RIR and actual reps/weight/RIR | add planned/actual duration and distance |
| actual validation | completed rows require `actual_reps` and `actual_rir` | require matching dimension; RIR not universal |
| planned-vs-actual summary | only below/inside/above rep range | keep rep-only metrics and add neutral time/distance deltas |
| set intelligence | missing reps/RIR lowers quality for all rows | exclude non-rep rows from rep/RIR penalties |
| progression decision | prescription/evidence require reps and RIR | neutral unsupported result for non-rep v1 |
| API routes | actual/progression payloads expose reps/RIR | add type-specific fields/invariants |
| frontend types | preview, planned, actual, summary, progression are rep-centric | add type-aware fields |
| `WorkoutPreviewExperience.tsx` | displays/seeds/submits reps/RIR and rep summaries | switch labels, inputs, defaults, and summaries by type |
| `frontend/src/app/page.tsx` | compact rows render planned/logged reps and RIR | render selected type/unit |

## 20. Proposed implementation-v1 contracts

### Canonical measurement metadata

```text
default_measurement_mode: reps | duration | distance
allowed_measurement_modes: ordered set of those values
sets_applicable: yes
load_applicability: applicable | optional | not_applicable | ambiguous
rir_applicability: applicable | not_applicable | ambiguous
distance_unit: meters when distance is allowed
```

Metadata describes defaults/constraints and must not silently select protocol.

### Candidate and approved planned exercise

Preserve current rep/RIR names for minimal compatibility and add:

```text
measurement_type: reps | duration | distance
sets: integer >= 1

reps_min: integer | null
reps_max: integer | null
target_duration_seconds: integer | null
target_distance_meters: number | null
rir_min: integer | null
rir_max: integer | null
```

The provider JSON may retain `target_rir_min` / `target_rir_max` and map to internal `rir_min` / `rir_max`.

| Type | Required target | Must be null | RIR |
| --- | --- | --- | --- |
| reps | positive ordered rep range | duration, distance | nullable; pair-valid when present |
| duration | positive seconds | reps, distance | null in v1 |
| distance | positive meters | reps, duration | null in v1 |

Exactly one target dimension is populated. The type must be catalog-allowed. Protocol and locomotion values are invalid types.

### Persisted planned exercise

Add nullable `measurement_type`, `target_duration_seconds`, and `target_distance_meters`. Keep current legacy rep/RIR columns during v1. Existing rows with `measurement_type IS NULL` are interpreted as `reps` and are not rewritten.

### Execution actual

Add:

```text
measurement_type
planned_duration_seconds
planned_distance_meters
actual_duration_seconds
actual_distance_meters
```

Keep existing planned/actual reps, weight, and RIR. Completed non-skipped rows require the actual field matching the type; skipped rows require none. Weight remains optional. Non-rep RIR stays null in v1.

### Planned-vs-actual summary

Keep current rep-deviation fields for `reps` rows only. Add neutral aggregates rather than treating longer/farther as automatically better:

```text
duration_comparable_set_count
duration_delta_seconds_total
distance_comparable_set_count
distance_delta_meters_total
```

Completion counts remain type-independent. Pace, work-rate, and adherence scoring are deferred.

## 21. Backward compatibility and migration

Existing data remains untouched:

- JSON without `measurement_type` reads as legacy `reps`.
- Existing selected plans and planned rows remain rep-mode records even if catalog defaults change.
- Existing actuals, history, and progression remain rep-mode truth.
- No historical record is reclassified from its exercise name.
- Canonical IDs and taxonomy remain stable.

### Strictly additive planned-row migration

Because current planned rep/RIR columns are non-null and destructive replacement is out of scope, use a temporary explicit compatibility sentinel for newly created non-rep rows:

```text
legacy reps_min/reps_max = 0/0
legacy rir_min/rir_max = 0/0
measurement_type = duration or distance
real target stored only in the matching new column
```

The sentinel is never a target and must never be rendered, summarized, or progressed. Every reader branches on `measurement_type` first. Positive rep validation remains for rep mode.

**Uncertainty:** Architecture may instead authorize a later transactional migration to nullable rep/RIR columns. That is cleaner but not strictly additive. This audit recommends the guarded sentinel for the initial additive release and separately reviewed cleanup later.

Safe rollout:

1. Add schema/model/API fields and legacy `NULL → reps` decoding.
2. Make persistence, summaries, progression guards, frontend types, and UI type-aware.
3. Prove legacy selected/completed plans unchanged.
4. Enable deterministic duration/distance generation.
5. Keep provider-generated non-rep plans disabled until parser/validator coverage is proven.

## 22. Progression recommendation

V1 should support correct planning, logging, completion, and history for duration/distance, but not automated non-rep progression.

For `measurement_type != reps`, return bounded neutral output such as:

```text
decision = insufficient_data
reason_code = unsupported_measurement_type_for_progression_v1
```

Do not reinterpret seconds/meters as reps, infer load changes, or generate pace/distance progression. Rep-mode behavior remains unchanged.

## 23. Workout UI impact

Display examples:

```text
reps:     3 sets • 8–10 reps • RIR 2–4
duration: 3 sets • 30 sec
distance: 3 sets • 40 m
```

Actual forms show one primary input by type: Reps, Duration, or Distance. Weight appears when useful but remains optional. RIR appears only for an applicable rep-mode plan. Notes and skip remain available for every type.

Today rows, edit forms, logged-set summaries, completion review, and planned-vs-actual panels use the same formatter. Non-rep rows must not show `0 reps`, fake RIR, or rep-range status. Progression UI hides or neutrally explains unsupported non-rep v1 decisions.

## 24. Recommended implementation sequence

1. Architecture accepts or corrects this matrix and the decisions below.
2. Add immutable catalog measurement metadata with exact-coverage tests.
3. Add singular type and nullable type-specific targets to candidate/approved models.
4. Add type-aware deterministic generation, provider parsing, and validation behind a gate.
5. Add planned/actual persistence fields and legacy decoding.
6. Add API/frontend types and type-aware preview/log/edit/summary UI.
7. Exclude non-rep rows from rep metrics and missing-rep/RIR penalties.
8. Add neutral non-rep progression guard.
9. Run isolated migration/regression/browser validation, then enable non-rep generation.

Do not begin runtime implementation until Architecture accepts this audit.

## 25. Implementation-v1 scope and non-goals

Recommended scope:

- singular `reps`, `duration`, or `distance` type;
- catalog default plus allowed modes;
- rep ranges;
- exact duration seconds and distance meters;
- sets as work blocks;
- optional independent weight;
- nullable/type-aware RIR;
- type-aware plan, persistence, actual logging, summaries, and UI;
- legacy rep-data preservation;
- neutral unsupported progression for non-rep work.

Non-goals:

- `duration_distance` simultaneous targets;
- duration/distance ranges;
- pace, speed, watts, heart rate, calories, cadence, resistance, incline, or grade targets;
- device telemetry/comparability;
- protocol normalization or interval segments;
- automated non-rep progression;
- load-system redesign;
- historical inference/backfill;
- canonical ID, taxonomy, media, substitution, familiarity, or preference changes.

## 26. Required worked examples

| Canonical exercise | Family / base | Default | Allowed | Sets | Load | RIR | Protocol distinction/reasoning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Barbell Bench Press | horizontal_press / bench_press | reps | reps | yes | applicable | applicable | conventional loaded press |
| Dumbbell Bench Press | horizontal_press / bench_press | reps | reps | yes | applicable | applicable | conventional loaded press |
| Plank | core_anti_extension / plank | duration | duration | yes | optional | not_applicable | static brace |
| Wall Sit | bilateral_knee_dominant / wall_sit | duration | duration | yes | optional | not_applicable | isometric knee-dominant work |
| Dead Hang | vertical_pull / bar_hang | duration | duration | yes | optional | not_applicable | passive hang; alias question does not alter mode |
| Farmer Carry | loaded_carry / farmer_carry | distance | duration or distance | yes | applicable | not_applicable | walk carry; load is separate |
| Suitcase Carry | loaded_carry / suitcase_carry | distance | duration or distance | yes | applicable | not_applicable | unilateral walk carry |
| Dumbbell Farmer March | loaded_carry / farmer_carry | reps | reps or duration | yes | applicable | ambiguous | in-place march differs from carry |
| Treadmill Walk | treadmill_locomotion / treadmill_walk | duration | duration or distance | yes | not_applicable | not_applicable | walk is locomotion, not measurement |
| Treadmill Easy Jog | treadmill_locomotion / treadmill_jog | duration | duration or distance | yes | not_applicable | not_applicable | easy is protocol; jog is locomotion |
| Treadmill Intervals | treadmill_locomotion / treadmill_locomotion_unspecified | duration | duration or distance | yes | not_applicable | not_applicable | intervals are protocol; locomotion unspecified |
| Bike Steady State | stationary_cycling / stationary_bike | duration | duration or distance | yes | not_applicable | not_applicable | steady_state protocol; distance device-reported |
| Bike Intervals | stationary_cycling / stationary_bike | duration | duration or distance | yes | not_applicable | not_applicable | intervals are protocol |
| Bear Crawl | quadrupedal_locomotion / bear_crawl | distance | duration or distance | yes | not_applicable | not_applicable | distance-first; timed-space alternative |
| Mountain Climber | ground_conditioning / mountain_climber | duration | reps or duration | yes | not_applicable | not_applicable | timed conditioning; contacts valid |
| Cat-Cow | mobility / cat_cow | reps | reps | yes | not_applicable | not_applicable | dynamic mobility cycles |
| Half-Kneeling Hip Flexor Stretch | mobility / hip_flexor_stretch | duration | duration | yes | not_applicable | not_applicable | static stretch |
| 90/90 Hip Switch | mobility / hip_90_90_switch | reps | reps | yes | not_applicable | not_applicable | dynamic switches |
| Band Shoulder Dislocate | shoulder_mobility / shoulder_dislocate | reps | reps | yes | not_applicable | not_applicable | dynamic passes; band is an implement |

## 27. Open Architecture decisions

1. Accept exactly three v1 types: `reps`, `duration`, `distance`.
2. Accept singular planned measurement and reject `duration_distance`.
3. Accept catalog default plus bounded allowed modes.
4. Accept the 31 multi-mode rows and duration-only Bike Cadence Drill.
5. Accept exact scalar duration/distance targets.
6. Accept meters as canonical storage with UI conversion.
7. Accept sets as work blocks for all 240 identities.
8. Accept nullable/type-aware RIR and no non-rep RIR in v1.
9. Accept optional independent weight without resistance redesign.
10. Choose guarded zero sentinels or authorize a later nullable-column migration.
11. Accept neutral unsupported non-rep progression.
12. Accept deferred secondary observations and protocol segments.

## 28. Matrix integrity result

Programmatic validation against repository truth produced:

```text
catalog names: 240
unique catalog names: 240
taxonomy rows: 240
unique taxonomy names: 240
measurement rows: 240
unique measurement names: 240
missing canonical names: 0
unknown canonical names: 0
empty default modes: 0
default-not-allowed errors: 0
invalid controlled values: 0
distance rows without meters: 0
protocol terms used as measurement modes: 0
locomotion terms used as measurement modes: 0
```

All 16 protocol candidates are present. Every static/isometric and dynamic-mobility identity was explicitly reviewed. No database or external provider was accessed.
