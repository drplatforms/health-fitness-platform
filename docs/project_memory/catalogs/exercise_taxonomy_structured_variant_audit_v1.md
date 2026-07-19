# Exercise Taxonomy & Structured Variant Audit v1

Status: revised evidence and architecture recommendation only. No runtime catalog, IDs, schema, migrations, database, provider, API, UI, media mapping, substitution, progression, or familiarity behavior changed.

## Executive summary and definitions

**Repository fact:** `CURATED_EXERCISE_CATALOG` has 240 canonical entries. The matrix has one exact source-backed row per entry.

**Recommendation:** distinguish five concepts. A **family** is a broader mechanically meaningful substitution/progression neighborhood. A **base movement** is the specific physical template within that neighborhood. **Physical variants** describe equipment, setup, or execution. **Prescription** describes workout dosing/protocol. A **visual identity** is an explicit physical demonstration identity. Family and base movement are deliberately different fields.

This corrected review avoids name-token equivalence: split squats and skater squats sit in a unilateral knee-dominant family, band lateral/monster walks in hip abduction, hamstring curls in knee flexion, Pike Push-Up in vertical press, High Pull in vertical power pull, and Band Dead Bug Pulldown in anti-extension core. Materially distinct exercises no longer share an identical family/base/physical-attribute representation.

## Family inventory

| Family | Definition | Members | Representative members | Distinct base movements |
| --- | --- | --- | --- | --- |
| horizontal_press | Broader mechanically meaningful substitution/progression neighborhood. | 24 | Push-Up, Incline Push-Up, Dumbbell Bench Press, Incline Dumbbell Press | bench_press, machine_chest_press, push_up, squeeze_press, standing_chest_press |
| elbow_flexion | Broader mechanically meaningful substitution/progression neighborhood. | 18 | Dumbbell Curl, EZ-Bar Curl, Cable Curl, Dumbbell Hammer Curl | concentration_curl, curl, drag_curl, hammer_curl, preacher_curl, reverse_curl, spider_curl, zottman_curl |
| rowing | Broader mechanically meaningful substitution/progression neighborhood. | 14 | Inverted Row, One-Arm Dumbbell Row, Dumbbell Row, Chest-Supported Dumbbell Row | barbell_row, cable_row, dumbbell_row, high_row, pendlay_row, renegade_row, row |
| bilateral_knee_dominant | Broader mechanically meaningful substitution/progression neighborhood. | 15 | Bodyweight Squat, Goblet Squat, Barbell Squat, Back Squat | back_squat, barbell_squat_unspecified, goblet_squat, leg_press, squat, wall_sit |
| unilateral_knee_dominant | Broader mechanically meaningful substitution/progression neighborhood. | 16 | Reverse Lunge, Split Squat, Dumbbell Split Squat, Dumbbell Skater Squat | lateral_lunge, lunge, reverse_lunge, skater_squat, split_squat, step_up, walking_lunge |
| vertical_pull | Broader mechanically meaningful substitution/progression neighborhood. | 15 | Pull-Up, Chin-Up, Commando Pull-Up, Cable Lat Pulldown | bar_hang, chin_up, commando_pull_up, flexed_arm_hang, lat_pulldown, pull_up, straight_arm_pulldown |
| hip_hinge | Broader mechanically meaningful substitution/progression neighborhood. | 13 | Dumbbell RDL, Romanian Deadlift, Conventional Deadlift, Dumbbell Single-Leg RDL | conventional_deadlift, deadlift, good_morning, hip_hinge_drill, pull_through, rack_pull, romanian_deadlift |
| elbow_extension | Broader mechanically meaningful substitution/progression neighborhood. | 13 | Dumbbell Triceps Extension, EZ-Bar Skull Crusher, Band Triceps Pressdown, Cable Triceps Pressdown | dip, jm_press, overhead_triceps_extension, skull_crusher, tate_press, triceps_extension, triceps_kickback, triceps_pressdown |
| core_anti_extension | Broader mechanically meaningful substitution/progression neighborhood. | 9 | Plank, Dead Bug, Hollow Body Hold, Barbell Rollout | band_dead_bug_pulldown, dead_bug, hollow_hold, plank, rollout, stir_the_pot |
| treadmill_locomotion | Broader mechanically meaningful substitution/progression neighborhood. | 8 | Treadmill Walk, Treadmill Incline Walk, Treadmill Intervals, Treadmill Easy Jog | treadmill_jog, treadmill_locomotion_unspecified, treadmill_run, treadmill_walk |
| vertical_press | Broader mechanically meaningful substitution/progression neighborhood. | 8 | Dumbbell Shoulder Press, Overhead Press, Pike Push-Up, Arnold Press | arnold_press, overhead_press, pike_push_up, push_press |
| hip_extension | Broader mechanically meaningful substitution/progression neighborhood. | 7 | Glute Bridge, Hip Thrust, Single-Leg Glute Bridge, Dumbbell Hip Thrust | glute_bridge, glute_kickback, hip_thrust |
| loaded_carry | Broader mechanically meaningful substitution/progression neighborhood. | 7 | Farmer Carry, Suitcase Carry, Waiter Carry, Dumbbell Front Rack Carry | farmer_carry, front_rack_carry, pinch_grip_carry, suitcase_carry, waiter_carry |
| rear_delt_retraction | Broader mechanically meaningful substitution/progression neighborhood. | 8 | Band Pull-Apart, Band Face Pull, Cable Rear Delt Row, Dumbbell Rear Delt Fly | band_pull_apart, face_pull, rear_delt_fly, rear_delt_row |
| stationary_cycling | Broader mechanically meaningful substitution/progression neighborhood. | 7 | Bike Steady State, Bike Intervals, Bike Recovery Ride, Bike Tempo Ride | stationary_bike |
| trunk_flexion | Broader mechanically meaningful substitution/progression neighborhood. | 7 | Hanging Knee Raise, Hollow Rock, Hanging Leg Raise, Cable Crunch | cable_crunch, hanging_knee_raise, hanging_leg_raise, heel_tap, hollow_rock, reverse_crunch, seated_knee_tuck |
| shoulder_elevation | Broader mechanically meaningful substitution/progression neighborhood. | 9 | Dumbbell Lateral Raise, Cable Lateral Raise, Dumbbell Front Raise, Dumbbell Upright Row | front_raise, lateral_raise, shoulder_raise, upright_row, y_raise |
| core_anti_rotation | Broader mechanically meaningful substitution/progression neighborhood. | 6 | Bird Dog, Band Pallof Press, Cable Pallof Press, Plank Shoulder Tap | anti_rotation_hold, bird_dog, pallof_press, plank_shoulder_tap |
| mobility | Broader mechanically meaningful substitution/progression neighborhood. | 5 | Cat-Cow, Quadruped T-Spine Rotation, Half-Kneeling Hip Flexor Stretch, 90/90 Hip Switch | cat_cow, childs_pose_lat_stretch, hip_90_90_switch, hip_flexor_stretch, quadruped_t_spine_rotation |
| shoulder_rotation | Broader mechanically meaningful substitution/progression neighborhood. | 4 | Band External Rotation, Cable External Rotation, Cable Internal Rotation, Cable 90/90 External Rotation | external_rotation, internal_rotation, shoulder_90_90_external_rotation |
| ankle_plantarflexion | Broader mechanically meaningful substitution/progression neighborhood. | 3 | Standing Calf Raise, Dumbbell Calf Raise, Barbell Calf Raise | calf_raise |
| chest_fly | Broader mechanically meaningful substitution/progression neighborhood. | 3 | Dumbbell Fly, Incline Dumbbell Fly, Cable Chest Fly | chest_fly |
| shoulder_mobility | Broader mechanically meaningful substitution/progression neighborhood. | 3 | Prone Y-T-W Raise, Wall Slide, Band Shoulder Dislocate | prone_y_t_w_raise, shoulder_dislocate, wall_slide |
| gait_drill | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Toe Walk, Heel Walk | heel_walk, toe_walk |
| hip_abduction | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Band Lateral Walk, Band Monster Walk | lateral_walk, monster_walk |
| knee_flexion | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Stability Ball Hamstring Curl, Band Hamstring Curl | hamstring_curl |
| lateral_core_stability | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Side Plank, Side Plank Reach-Through | side_plank |
| rotational_core | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Cable Woodchop, Band Woodchop | woodchop |
| scapular_elevation | Broader mechanically meaningful substitution/progression neighborhood. | 2 | Dumbbell Shrug, Barbell Shrug | shrug |
| back_extension | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Superman Hold | superman_hold |
| ground_conditioning | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Mountain Climber | mountain_climber |
| lateral_trunk_flexion | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Hanging Oblique Knee Raise | hanging_oblique_knee_raise |
| quadrupedal_locomotion | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Bear Crawl | bear_crawl |
| shoulder_extension | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Dumbbell Pullover | dumbbell_pullover |
| vertical_power_pull | Broader mechanically meaningful substitution/progression neighborhood. | 1 | Barbell High Pull | high_pull |

## Structured dimension recommendation

Keep existing equipment first class. Use compact controlled values for **body_position** and distinct **support_type**, plus bench_angle, laterality, grip, stance, load_position, attachment, movement_direction, locomotion_mode, and execution_mode (dynamic/isometric/eccentric-only). Keep a controlled extension for infrequent range/elevation/grade detail. The final collision pass used this existing vocabulary for wall support, chest/thigh support, low-incline angle, cross-body/high-diagonal/rotational paths, carry walk-versus-march mode, and partial rack-pull range. No additional controlled dimension is proposed for v1.

## Dispositions and protocol audit

| Disposition | Count |
| --- | --- |
| RETAIN_DISTINCT | 12 |
| RETAIN_AS_STRUCTURED_VARIANT | 205 |
| PRESCRIPTION_OR_PROTOCOL_CANDIDATE | 16 |
| ALIAS_OR_DUPLICATE_CANDIDATE | 3 |
| TAXONOMY_REVIEW_REQUIRED | 4 |

| Canonical identity | Physical base movement | Protocol | Migration concern |
| --- | --- | --- | --- |
| Treadmill Intervals | treadmill_locomotion_unspecified | protocol=intervals | Preserve ID/history and unspecified walk/jog/run mode; future prescription link must be additive. |
| Bike Steady State | stationary_bike | protocol=steady_state | Preserve ID/history; future prescription link must be additive. |
| Bike Intervals | stationary_bike | protocol=intervals | Preserve ID/history; future prescription link must be additive. |
| Tempo Push-Up | push_up | protocol=tempo | Preserve ID/history; future prescription link must be additive. |
| Pause Squat | barbell_squat | protocol=pause | Preserve ID/history; future prescription link must be additive. |
| Treadmill Easy Jog | treadmill_jog | protocol=easy | Preserve ID/history; future prescription link must be additive. |
| Treadmill Hill Intervals | treadmill_locomotion_unspecified | protocol=hill_intervals | Preserve ID/history and unspecified walk/jog/run mode; future prescription link must be additive. |
| Treadmill Tempo Run | treadmill_run | protocol=tempo | Preserve ID/history; future prescription link must be additive. |
| Bike Recovery Ride | stationary_bike | protocol=recovery | Preserve ID/history; future prescription link must be additive. |
| Bike Tempo Ride | stationary_bike | protocol=tempo | Preserve ID/history; future prescription link must be additive. |
| Bike Hill Intervals | stationary_bike | protocol=hill_intervals | Preserve ID/history; future prescription link must be additive. |
| Dumbbell Tempo Goblet Squat | goblet_squat | protocol=tempo | Preserve ID/history; future prescription link must be additive. |
| Treadmill Recovery Walk | treadmill_walk | protocol=recovery | Preserve ID/history; future prescription link must be additive. |
| Treadmill Easy Intervals | treadmill_locomotion_unspecified | protocol=easy_intervals | Preserve ID/history and unspecified walk/jog/run mode; future prescription link must be additive. |
| Bike Easy Spin | stationary_bike | protocol=easy | Preserve ID/history; future prescription link must be additive. |
| Bike Cadence Drill | stationary_bike | protocol=cadence_drill | Preserve ID/history; future prescription link must be additive. |

`Treadmill Easy Jog` explicitly retains `locomotion_mode=jog` while recording `protocol=easy`; walk, jog, and run remain physically distinct.

## Structured-representation collision audit

Collision key: exact equality of `family + base_movement + physical_variant_attributes`, with prescription intentionally excluded. The 27 non-protocol duplicate groups identified by Architecture were manually reviewed as follows; none was resolved with an arbitrary uniqueness attribute.

| Initial collision group | Manual resolution |
| --- | --- |
| Barbell Squat / Back Squat | `barbell_squat_unspecified` versus `back_squat`; Pause Squat uses the same under-specified physical base only as an explicit protocol variant. |
| Rope Triceps Pressdown / Rope Overhead Triceps Extension | `triceps_pressdown` versus `overhead_triceps_extension`. |
| Dumbbell Skull Crusher / Dumbbell Tate Press | `skull_crusher` versus `tate_press`. |
| EZ-Bar Skull Crusher / EZ-Bar JM Press | `skull_crusher` versus `jm_press`. |
| Band Triceps Pressdown / Band Overhead Triceps Extension | `triceps_pressdown` versus `overhead_triceps_extension`. |
| Dumbbell Curl / Dumbbell Concentration Curl / Dumbbell Zottman Curl | `curl`, `concentration_curl` with thigh support, and `zottman_curl`. |
| Dumbbell Hammer Curl / Dumbbell Cross-Body Hammer Curl | Shared `hammer_curl`; cross-body direction is explicit on the latter. |
| EZ-Bar Curl / EZ-Bar Drag Curl | `curl` versus `drag_curl`. |
| Romanian Deadlift / Conventional Deadlift | `romanian_deadlift` versus `conventional_deadlift`; Dumbbell/Band/Cable RDL rows also use `romanian_deadlift`. |
| Barbell Good Morning / Rack Pull | `good_morning` versus `rack_pull`, with partial range explicit on Rack Pull. |
| Band Pull-Through / Band Good Morning | `pull_through` versus `good_morning`; Cable Pull-Through also uses `pull_through`. |
| Dumbbell Bench Press / Dumbbell Squeeze Press | `bench_press` versus `squeeze_press`. |
| Incline Dumbbell Press / Low-Incline Dumbbell Press | Shared `bench_press`; `bench_angle=incline` versus `bench_angle=low_incline`. |
| Push-Up / Wall Push-Up | Shared `push_up`; Wall Push-Up has standing body position and wall support. |
| Side Plank / Side Plank Reach-Through | Shared `side_plank`; isometric versus dynamic rotational execution. |
| Farmer Carry / Dumbbell Farmer March | Shared `farmer_carry`; walk versus march locomotion mode. |
| Suitcase Carry / Waiter Carry / Dumbbell Suitcase March | `suitcase_carry` versus `waiter_carry`, with suitcase/overhead load position and walk/march mode explicit. |
| Barbell Row / Pendlay Row | `barbell_row` versus `pendlay_row`. |
| Cable Row / Cable High Row / Cable Rear Delt Row | `cable_row`, `high_row`, and `rear_delt_row`; Rear Delt Row moves to `rear_delt_retraction`. |
| Dumbbell Row / Dumbbell Renegade Row | `dumbbell_row` versus plank-position `renegade_row`. |
| Chest-Supported Dumbbell Row / Chest-Supported Row | Preserved as a documented alias candidate pending catalog-owner evidence. |
| Cable Lateral Raise / Cable Y Raise | `lateral_raise` versus `y_raise`. |
| Dumbbell Lateral Raise / Dumbbell Front Raise | `lateral_raise` versus `front_raise`. |
| Dumbbell Shoulder Press / Arnold Press | `overhead_press` versus `arnold_press`. |
| Dead Hang / Pull-Up Bar Dead Hang | Preserved as a documented alias candidate pending catalog-owner evidence. |
| Cable Lat Pulldown / Lat Pulldown | Preserved as a documented alias candidate pending catalog-owner evidence. |
| Pull-Up / Chin-Up / Commando Pull-Up | `pull_up`, `chin_up`, and `commando_pull_up`, with pronated/supinated/mixed grip evidence. |

The separately mandated Dumbbell Skater Squat correction places it in `unilateral_knee_dominant` with base `skater_squat` and unilateral laterality. Generic `hinge` no longer hides Good Morning, Pull-Through, or Rack Pull templates.

After correction, every remaining exact duplicate representation is an allowed exception:

| Final duplicate group | Classification | Why retained |
| --- | --- | --- |
| Barbell Squat / Pause Squat | PRESCRIPTION_ONLY | Same under-specified physical template; `protocol=pause` is the distinction. Visual identities remain separate because the base identity is review-required. |
| Goblet Squat / Dumbbell Tempo Goblet Squat | PRESCRIPTION_ONLY | Same physical goblet squat; `protocol=tempo` is the distinction. |
| Push-Up / Tempo Push-Up | PRESCRIPTION_ONLY | Same physical push-up; `protocol=tempo` is the distinction. |
| Chest-Supported Dumbbell Row / Chest-Supported Row | LEGITIMATE_ALIAS | Explicit alias candidate; canonical identities remain separate until confirmed. |
| Bike Steady State / Bike Intervals / Bike Recovery Ride / Bike Tempo Ride / Bike Hill Intervals / Bike Easy Spin / Bike Cadence Drill | PRESCRIPTION_ONLY | Same stationary-bike demonstration; protocol carries the distinction. |
| Treadmill Intervals / Treadmill Easy Intervals | PRESCRIPTION_ONLY | Same explicitly unspecified treadmill-locomotion template; protocol carries the distinction. |
| Treadmill Walk / Treadmill Recovery Walk | PRESCRIPTION_ONLY | Same treadmill-walk template; `protocol=recovery` is the distinction. |
| Dead Hang / Pull-Up Bar Dead Hang | LEGITIMATE_ALIAS | Explicit alias candidate; canonical identities and visuals remain separate until confirmed. |
| Cable Lat Pulldown / Lat Pulldown | LEGITIMATE_ALIAS | Explicit alias candidate; canonical identities and visuals remain separate until confirmed. |

Final collision invariant: **9** duplicate structured-representation groups = **3 LEGITIMATE_ALIAS + 6 PRESCRIPTION_ONLY + 0 ERROR**.

## Alias and taxonomy review candidates

| Canonical identity | Disposition | Reason |
| --- | --- | --- |
| Chest-Supported Row | ALIAS_OR_DUPLICATE_CANDIDATE | Possible equivalent to Chest-Supported Dumbbell Row; remains separate until setup/instruction/media review confirms an alias. |
| Barbell Squat | TAXONOMY_REVIEW_REQUIRED | Umbrella name beside Back Squat needs catalog-owner definition. |
| Cable Lat Pulldown | ALIAS_OR_DUPLICATE_CANDIDATE | Possible equivalent to Lat Pulldown; remains separate until setup/instruction/media review confirms an alias. |
| Standing Calf Raise | TAXONOMY_REVIEW_REQUIRED | Current conditioning pattern conflicts with calf-raise semantics. |
| Dumbbell Calf Raise | TAXONOMY_REVIEW_REQUIRED | Current conditioning pattern conflicts with calf-raise semantics. |
| Dead Hang | ALIAS_OR_DUPLICATE_CANDIDATE | Possible equivalent to Pull-Up Bar Dead Hang; remains separate until setup/instruction/media review confirms an alias. |
| Cable Kickback | TAXONOMY_REVIEW_REQUIRED | Name is under-specified between glute and triceps uses; current hinge placement suggests glute. |

## Conservative visual-identity audit

Default: every canonical identity has its own visual identity. The only sharing groups are manually reviewed protocol-only cases where the physical movement is unchanged: Tempo Push-Up/Push-Up; Dumbbell Tempo Goblet Squat/Goblet Squat; Treadmill Recovery Walk/Treadmill Walk; and stationary-bike prescription forms using neutral `visual_stationary_bike`. Pause Squat remains separate because unresolved Barbell Squat cannot anchor shared visual media. Possible aliases remain separate. No sharing is derived from family, equipment, or sparse attributes.

Result: **231** candidate visual identities; **4** manually defensible sharing groups containing **13** canonical identities. Pull-up/chin-up/hang, core, mobility, press, row, pulldown, lunge, and hanging-raise examples named in Architecture review remain separate.

## Worked examples

| Canonical | Family | Base movement | Physical variants | Prescription | Visual identity | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| Dumbbell Bench Press | horizontal_press | bench_press | equipment=dumbbell+adjustable_bench; support_type=bench | — | visual_dumbbell_bench_press | RETAIN_DISTINCT |
| Incline Dumbbell Press | horizontal_press | bench_press | equipment=dumbbell+adjustable_bench; support_type=bench; bench_angle=incline | — | visual_incline_dumbbell_press | RETAIN_AS_STRUCTURED_VARIANT |
| Machine Chest Press | horizontal_press | machine_chest_press | equipment=machine; support_type=machine | — | visual_machine_chest_press | RETAIN_AS_STRUCTURED_VARIANT |
| Pike Push-Up | vertical_press | pike_push_up | equipment=bodyweight | — | visual_pike_push_up | RETAIN_AS_STRUCTURED_VARIANT |
| Push Press | vertical_press | push_press | equipment=barbell+rack+plates; execution_mode=dynamic; lower_body_drive=deliberate | — | visual_push_press | RETAIN_AS_STRUCTURED_VARIANT |
| One-Arm Dumbbell Row | rowing | row | equipment=dumbbell+adjustable_bench; support_type=bench; laterality=unilateral | — | visual_one_arm_dumbbell_row | RETAIN_DISTINCT |
| Cable High Row | rowing | high_row | equipment=cable; movement_direction=high_diagonal | — | visual_cable_high_row | RETAIN_AS_STRUCTURED_VARIANT |
| Cable Rear Delt Row | rear_delt_retraction | rear_delt_row | equipment=cable; movement_direction=horizontal | — | visual_cable_rear_delt_row | RETAIN_AS_STRUCTURED_VARIANT |
| Lat Pulldown | vertical_pull | lat_pulldown | equipment=cable | — | visual_lat_pulldown | RETAIN_AS_STRUCTURED_VARIANT |
| Straight-Arm Cable Pulldown | vertical_pull | straight_arm_pulldown | equipment=cable | — | visual_straight_arm_cable_pulldown | RETAIN_AS_STRUCTURED_VARIANT |
| Split Squat | unilateral_knee_dominant | split_squat | equipment=bodyweight; stance=split | — | visual_split_squat | RETAIN_AS_STRUCTURED_VARIANT |
| Dumbbell Skater Squat | unilateral_knee_dominant | skater_squat | equipment=dumbbell; laterality=unilateral | — | visual_dumbbell_skater_squat | RETAIN_AS_STRUCTURED_VARIANT |
| Romanian Deadlift | hip_hinge | romanian_deadlift | equipment=barbell+plates | — | visual_romanian_deadlift | RETAIN_DISTINCT |
| Conventional Deadlift | hip_hinge | conventional_deadlift | equipment=barbell+plates | — | visual_conventional_deadlift | RETAIN_AS_STRUCTURED_VARIANT |
| Band Lateral Walk | hip_abduction | lateral_walk | equipment=resistance_band; locomotion_mode=walk | — | visual_band_lateral_walk | RETAIN_AS_STRUCTURED_VARIANT |
| Stability Ball Hamstring Curl | knee_flexion | hamstring_curl | equipment=exercise_ball | — | visual_stability_ball_hamstring_curl | RETAIN_AS_STRUCTURED_VARIANT |
| Band Dead Bug Pulldown | core_anti_extension | band_dead_bug_pulldown | equipment=bodyweight+resistance_band | — | visual_band_dead_bug_pulldown | RETAIN_AS_STRUCTURED_VARIANT |
| Plank | core_anti_extension | plank | equipment=bodyweight | — | visual_plank | RETAIN_DISTINCT |
| Hollow Rock | trunk_flexion | hollow_rock | equipment=bodyweight | — | visual_hollow_rock | RETAIN_AS_STRUCTURED_VARIANT |
| Treadmill Easy Jog | treadmill_locomotion | treadmill_jog | equipment=treadmill; locomotion_mode=jog | protocol=easy | visual_treadmill_easy_jog | PRESCRIPTION_OR_PROTOCOL_CANDIDATE |
| Bike Cadence Drill | stationary_cycling | stationary_bike | equipment=bike | protocol=cadence_drill | visual_stationary_bike | PRESCRIPTION_OR_PROTOCOL_CANDIDATE |
| Cable Pallof Press | core_anti_rotation | pallof_press | equipment=cable; execution_mode=dynamic | — | visual_cable_pallof_press | RETAIN_AS_STRUCTURED_VARIANT |

## Downstream and migration implications

Future deterministic substitutions may score family proximity first, then explicit base-movement/variant distance; they must retain stable canonical IDs and explain ranking. Progression, history, familiarity, preferences, and approved media stay canonical-ID specific; family-level signals can only supplement them. Visual guidance may later link an identity to a reviewed visual target without collapsing logged identities. Provider matching can use internal structured facts, but providers remain non-authoritative.

Use an additive migration: catalog-ID-keyed family/base/variant metadata first, reviewed aliases/deprecations only later, and explicit prescription-template links separately. Name-sensitive catalog seeding, instruction/form-media seed validation, name lookup fallback, and history recency logic require alias-aware stable-ID migration review.

## Implementation-v1 scope, non-goals, and decisions

Recommended v1: read-only catalog metadata for family, base movement, controlled physical variants, explicit visual identities, and future prescription links. Non-goals: renames/deletions, runtime schema changes in this audit, automatic visual sharing, provider integration, workout behavior, or health recommendations.

Architecture decisions: exact Barbell Squat meaning; calf-raise pattern correction; Cable Kickback meaning; which prescription candidates remain selectable identities; whether family is a table or controlled metadata; and the accepted controlled vocabularies for movement direction, locomotion mode, and execution mode.

## Matrix integrity

CSV evidence: 240 rows, 240 unique canonical names, and exact source catalog coverage. The final matrix contains 35 non-synonymous family namespaces, 231 visual identities, and 4 manually reviewed sharing groups containing 13 canonical identities. Dispositions remain 12 distinct, 205 structured variants, 16 prescription/protocol candidates, 3 alias candidates, and 4 taxonomy-review-required identities. Confidence remains 216 high, 21 medium, and 3 low; low confidence is reserved for treadmill interval identities whose walk/jog/run physical mode is unspecified.

The full invariant sweep found no duplicate attribute keys, locomotion attributes on non-locomotion movements, dynamic repetitions marked isometric, protocol concepts used as physical base movements, review-required visual anchors, synonymous family namespaces, or unresolved material-exercise representation collisions. The exact collision inventory is 9 allowed groups: 3 `LEGITIMATE_ALIAS`, 6 `PRESCRIPTION_ONLY`, and 0 `ERROR`. `body_position` and `support_type` remain separate dimensions. No database or provider access was used.
