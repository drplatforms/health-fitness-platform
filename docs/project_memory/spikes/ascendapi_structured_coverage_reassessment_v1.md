# Structured AscendAPI Coverage Reassessment v1

Status: evidence spike complete; no production integration authorized or performed.

Recommendation: `SEMANTICALLY_READY_PROVIDER_RIGHTS_BLOCKED`.

## Decision summary

The accepted physical `visual_identity_slug` is the matching unit. Protocol and measurement metadata were used only as context. The official unauthenticated ExerciseDB V1 inventory still exposes 1,500 records and one 180p GIF per record. Structured review plus representative-frame inspection approves 46 provider assets for 46 visual identities and 52 canonical exercises. Combined with three already accepted internal visual-reuse opportunities, projected canonical coverage is 138 / 240. This is evidence for a future Visualization v2 ingestion milestone, not current runtime coverage.

Provider rights block ingestion: official free-tier documentation permits non-commercial use and requires AscendAPI attribution, while commercial/SaaS use requires a paid plan. The reviewed official pages do not expressly grant permanent local caching, vendoring, redistribution, or CDN mirroring rights.

## Scope and repository baseline

- Baseline: `main @ a38aefc` (`Merge exercise protocol templates v1`).
- Spike branch: `spike/structured-ascendapi-coverage-reassessment-v1`.
- Repository facts came only from the five runtime-owned manifests named by the handoff.
- No database, API, frontend, runtime provider integration, catalog identity, taxonomy, media projection, workout behavior, or dependency changed.

## Structured baseline reconciliation

| Invariant | Result |
| --- | ---: |
| Canonical exercises | 240 |
| Family namespaces | 35 |
| Accepted visual identities | 231 |
| Direct local-media-covered canonical exercises | 83 |
| Direct-uncovered canonical exercises | 157 |
| Visual identities represented by direct-uncovered exercises | 151 |
| Existing-local-reuse groups / canonical fan-out | 3 / 3 |
| True provider target visual identities / canonical exercises | 148 / 154 |

The three internal reuse groups reconcile exactly: `Tempo Push-Up -> visual_push_up`, `Dumbbell Tempo Goblet Squat -> visual_goblet_squat`, and `Treadmill Recovery Walk -> visual_treadmill_walk`. They are not counted as current runtime coverage. The accepted `visual_stationary_bike` group contains exactly Bike Steady State, Bike Intervals, Bike Recovery Ride, Bike Tempo Ride, Bike Hill Intervals, Bike Easy Spin, and Bike Cadence Drill.

## Provider verification and acquisition

Checked 2026-07-19:

- [AscendAPI landing page](https://exercisedb.dev/docs) identifies the no-key free API and 1,500-GIF inventory.
- [Official free V1 reference](https://oss.exercisedb.dev/docs) states 1,500 structured exercises, eight core fields, 180p GIFs, non-commercial use only, and attribution required.
- [Current V1 overview](https://docs.ascendapi.com/products/edb-v1/overview) distinguishes the unauthenticated 1,500-record free tier from the larger paid V1 offering.
- [Official pagination guide](https://docs.ascendapi.com/guides/pagination) defines `data`, `meta.total`, `hasNextPage`, `nextCursor`, and `after` cursor use.
- [Official rate-limit guide](https://docs.ascendapi.com/guides/ratelimiting) documents plan limits and separate CDN media handling.

Observed endpoint: `GET https://oss.exercisedb.dev/api/v1/exercises?limit=25[&after=<nextCursor>]`.

Observed response keys: `success`, `meta`, `data`. Observed exercise keys: `exerciseId`, `name`, `gifUrl`, `bodyParts`, `equipments`, `targetMuscles`, `secondaryMuscles`, `instructions`.

Acquisition used 60 cursor pages of 25 records, stopped at `hasNextPage=false`, and reconciled `meta.total=1500`, 1,500 acquired rows, and 1,500 unique exercise IDs. The endpoint imposed Cloudflare pacing stricter than a burst of 25-record calls; a seven-second cadence completed successfully. All ranking ran locally after acquisition.

## Matching and visual-review method

Each of the 151 groups joined exact repository-owned family, base movement, equipment, physical variants, extensions, protocol links, and measurement defaults/allowed modes. Candidate ranking used normalized name similarity, equipment compatibility, and muscle context; it never approved a mapping by score alone.

Hard gates covered equipment, body position, support, bench angle, laterality, grip, stance, load position, attachment, movement direction, locomotion, execution mode, grade, and range. For each approval, the provider GIF was fetched temporarily and three representative frames were inspected for setup and defining execution. Fifty-seven total prior/proposal/challenge assets were inspected; metadata-only hard mismatches did not need extra downloads. Temporary GIFs and contact sheets are not evidence artifacts and must be deleted at closeout.

## Final classification

| Bucket | Visual identities |
| --- | --- |
| existing_local_visual_reuse | 3 |
| ascendapi_approved_exact | 46 |
| review_required | 13 |
| rejected_material_mismatch | 57 |
| no_provider_candidate | 32 |

## Approved mappings

One row is one accepted provider asset / visual identity. The stationary-bike row explicitly fans one asset out to the already accepted seven-name identity; all other rows fan out to one canonical exercise. No new visual-sharing group was created.

| Visual identity | Canonical fan-out | Provider | Equipment | Decision |
| --- | --- | --- | --- | --- |
| visual_back_squat | Back Squat | `DhMl549` — barbell full squat (back pov) | barbell | new_structured_exact |
| visual_band_pallof_press | Band Pallof Press | `9pa4H5m` — band horizontal pallof press | band | retained_prior_exact |
| visual_band_pull_through | Band Pull-Through | `VtTbiP3` — band pull through | band | retained_prior_exact |
| visual_band_shoulder_press | Band Shoulder Press | `peAeMR3` — band shoulder press | band | retained_prior_exact |
| visual_band_squat | Band Squat | `TUZLh71` — band squat | band | new_structured_exact |
| visual_barbell_calf_raise | Barbell Calf Raise | `8ozhUIZ` — barbell standing calf raise | barbell | new_structured_exact |
| visual_barbell_reverse_lunge | Barbell Reverse Lunge | `VaP75jl` — barbell rear lunge | barbell | new_structured_exact |
| visual_bear_crawl | Bear Crawl | `0Yz8WdV` — bear crawl | body weight | new_structured_exact |
| visual_cable_chest_fly | Cable Chest Fly | `Pr9Rhf4` — cable standing fly | cable | new_structured_exact |
| visual_cable_external_rotation | Cable External Rotation | `FWdVhcW` — cable standing shoulder external rotation | cable | new_structured_exact |
| visual_cable_lat_pulldown | Cable Lat Pulldown | `qdRxqCj` — cable pulldown (pro lat bar) | cable | retained_prior_exact |
| visual_cable_lateral_raise | Cable Lateral Raise | `goJ6ezq` — cable lateral raise | cable | retained_prior_exact |
| visual_cable_pull_through | Cable Pull-Through | `OM46QHm` — cable pull through (with rope) | cable | new_structured_exact |
| visual_cable_upright_row | Cable Upright Row | `cALKspW` — cable upright row | cable | retained_prior_exact |
| visual_chest_supported_dumbbell_row | Chest-Supported Dumbbell Row | `7vG5o25` — dumbbell incline row | dumbbell | new_structured_exact |
| visual_chest_supported_rear_delt_fly | Chest-Supported Rear Delt Fly | `vYk8lqw` — dumbbell incline rear lateral raise | dumbbell | new_structured_exact |
| visual_close_grip_push_up | Close-Grip Push-Up | `x6KpKpq` — close-grip push-up | body weight | new_structured_exact |
| visual_dumbbell_calf_raise | Dumbbell Calf Raise | `dPmaUaU` — dumbbell standing calf raise | dumbbell | new_structured_exact |
| visual_dumbbell_cross_body_hammer_curl | Dumbbell Cross-Body Hammer Curl | `Qyk5J3p` — dumbbell cross body hammer curl | dumbbell | retained_prior_exact |
| visual_dumbbell_hammer_curl | Dumbbell Hammer Curl | `slDvUAU` — dumbbell hammer curl | dumbbell | retained_prior_exact |
| visual_dumbbell_pullover | Dumbbell Pullover | `9XjtHvS` — dumbbell pullover | dumbbell | new_structured_exact |
| visual_dumbbell_rdl | Dumbbell RDL | `rR0LJzx` — dumbbell romanian deadlift | dumbbell | new_structured_exact |
| visual_dumbbell_rear_delt_fly | Dumbbell Rear Delt Fly | `8DiFDVA` — dumbbell rear fly | dumbbell | retained_prior_exact |
| visual_dumbbell_reverse_curl | Dumbbell Reverse Curl | `0IgNjSM` — dumbbell standing reverse curl | dumbbell | new_structured_exact |
| visual_dumbbell_shoulder_press | Dumbbell Shoulder Press | `A6wtbuL` — dumbbell standing overhead press | dumbbell | new_structured_exact |
| visual_dumbbell_single_leg_rdl | Dumbbell Single-Leg RDL | `gKozT8X` — dumbbell single leg deadlift | dumbbell | new_structured_exact |
| visual_dumbbell_skull_crusher | Dumbbell Skull Crusher | `mpKZGWz` — dumbbell lying triceps extension | dumbbell | new_structured_exact |
| visual_ez_bar_jm_press | EZ-Bar JM Press | `hnOYgH3` — ez barbell jm bench press | ez barbell | new_structured_exact |
| visual_ez_bar_overhead_triceps_extension | EZ-Bar Overhead Triceps Extension | `iaapw0g` — ez barbell seated triceps extension | ez barbell | new_structured_exact |
| visual_ez_bar_reverse_curl | EZ-Bar Reverse Curl | `Y5X65IB` — ez barbell reverse grip curl | ez barbell | new_structured_exact |
| visual_hanging_knee_raise | Hanging Knee Raise | `VEcJRo2` — hanging leg hip raise | body weight | new_structured_exact |
| visual_hanging_oblique_knee_raise | Hanging Oblique Knee Raise | `BaE7O6U` — hanging oblique knee raise | body weight | retained_prior_exact |
| visual_heel_tap | Heel Tap | `qaZVsGk` — alternate heel touchers | body weight | new_structured_exact |
| visual_lat_pulldown | Lat Pulldown | `RVwzP10` — cable pulldown | cable | new_structured_exact |
| visual_machine_row | Machine Row | `7I6LNUG` — lever seated row | leverage machine | new_structured_exact |
| visual_neutral_grip_pull_up | Neutral-Grip Pull-Up | `0V2YQjW` — pull up (neutral grip) | body weight | retained_prior_exact |
| visual_pendlay_row | Pendlay Row | `r0z6xzQ` — barbell pendlay row | barbell | new_structured_exact |
| visual_plank_shoulder_tap | Plank Shoulder Tap | `yRpV5TC` — shoulder tap | body weight | new_structured_exact |
| visual_plate_front_raise | Plate Front Raise | `e4aFmFY` — weighted front raise | weighted | new_structured_exact |
| visual_rope_hammer_curl | Rope Hammer Curl | `HPlPoQA` — cable hammer curl (with rope) | cable | new_structured_exact |
| visual_scapular_push_up | Scapular Push-Up | `jV65tKx` — scapula push-up | body weight | new_structured_exact |
| visual_single_arm_cable_row | Single-Arm Cable Row | `EIsE3u8` — cable one arm bent over row | cable | new_structured_exact |
| visual_stationary_bike | Bike Steady State; Bike Intervals; Bike Recovery Ride; Bike Tempo Ride; Bike Hill Intervals; Bike Easy Spin; Bike Cadence Drill | `H1PESYI` — stationary bike run | stationary bike | new_structured_exact |
| visual_treadmill_incline_walk | Treadmill Incline Walk | `rjiM4L3` — walking on incline treadmill | leverage machine | new_structured_exact |
| visual_waiter_carry | Waiter Carry | `mWBtgmb` — dumbbell single arm overhead carry | dumbbell | new_structured_exact |
| visual_wall_push_up | Wall Push-Up | `LEH9jxP` — push-up (wall) | body weight | new_structured_exact |

## Coverage accounting

### Current runtime direct coverage

`83 / 240` canonical exercises. Runtime remains keyed directly by canonical exercise ID.

### Potential accepted internal reuse

`+3` canonical exercises, projecting `86 / 240` only if Visualization v2 adds explicit visual-identity resolution. This is not current runtime coverage and adds no new visual identity.

### Potential approved AscendAPI slice

- approved provider assets: 46;
- unique visual identities newly covered: 46;
- canonical exercises covered through accepted fan-out: 52;
- projected total after internal reuse plus provider mappings: `138 / 240` (57.5%);
- projected remaining canonical gaps: 102;
- projected remaining unique visual-identity gaps: 102.

## Prior exact revalidation

Eleven prior exact mappings remain approved. `Band Biceps Curl -> 3omWx6P` is downgraded because the GIF is explicitly alternating/unilateral while the accepted canonical identity has no reviewed alternating/laterality variant.

| Canonical | Prior | Structured result | Provider | Visual decision |
| --- | --- | --- | --- | --- |
| Band Biceps Curl | exact | rejected_material_mismatch | `3omWx6P` — band alternating biceps curl | alternating unilateral execution is materially narrower than the unqualified canonical curl |
| Band Pallof Press | exact | ascendapi_approved_exact | `9pa4H5m` — band horizontal pallof press | physical variants and representative frames compatible |
| Band Pull-Through | exact | ascendapi_approved_exact | `VtTbiP3` — band pull through | physical variants and representative frames compatible |
| Band Shoulder Press | exact | ascendapi_approved_exact | `peAeMR3` — band shoulder press | physical variants and representative frames compatible |
| Cable Lat Pulldown | exact | ascendapi_approved_exact | `qdRxqCj` — cable pulldown (pro lat bar) | physical variants and representative frames compatible |
| Cable Lateral Raise | exact | ascendapi_approved_exact | `goJ6ezq` — cable lateral raise | physical variants and representative frames compatible |
| Cable Upright Row | exact | ascendapi_approved_exact | `cALKspW` — cable upright row | physical variants and representative frames compatible |
| Dumbbell Cross-Body Hammer Curl | exact | ascendapi_approved_exact | `Qyk5J3p` — dumbbell cross body hammer curl | physical variants and representative frames compatible |
| Dumbbell Hammer Curl | exact | ascendapi_approved_exact | `slDvUAU` — dumbbell hammer curl | physical variants and representative frames compatible |
| Dumbbell Rear Delt Fly | exact | ascendapi_approved_exact | `8DiFDVA` — dumbbell rear fly | physical variants and representative frames compatible |
| Hanging Oblique Knee Raise | exact | ascendapi_approved_exact | `BaE7O6U` — hanging oblique knee raise | physical variants and representative frames compatible |
| Neutral-Grip Pull-Up | exact | ascendapi_approved_exact | `0V2YQjW` — pull up (neutral grip) | physical variants and representative frames compatible |

## Prior-versus-new reconciliation

The prior unit was 157 canonical names: 12 exact, 107 review, and 38 no match. The new unit is 151 visual identities, including three internal-reuse groups and one seven-name stationary-bike group, so raw bucket counts are not directly comparable.

- retained prior exact canonical mappings: 11;
- downgraded prior exact mappings: 1;
- newly approved provider visual identities: 35;
- newly approved provider canonical fan-out: 41;
- prior-review canonical exercises promoted by new provider approvals: 33;
- prior-no-match canonical exercises newly approved through provider mappings: 8;
- prior-no-match canonical exercises covered through accepted internal sharing: 2 (`Tempo Push-Up`, `Treadmill Recovery Walk`);
- prior-review canonical exercises covered through accepted internal sharing: 1 (`Dumbbell Tempo Goblet Squat`).

The CSV preserves the prior status for every canonical member of every group and records review/rejection/no-candidate outcomes individually.

## Remaining gaps

### Highest-volume families

| Family | Unresolved visual identities |
| --- | --- |
| unilateral_knee_dominant | 9 |
| elbow_flexion | 7 |
| vertical_pull | 7 |
| horizontal_press | 6 |
| core_anti_extension | 6 |
| rowing | 6 |
| bilateral_knee_dominant | 6 |
| mobility | 5 |
| loaded_carry | 5 |
| treadmill_locomotion | 5 |
| core_anti_rotation | 4 |
| rear_delt_retraction | 4 |

### Highest-volume equipment signatures

| Equipment signature | Unresolved visual identities |
| --- | --- |
| bodyweight | 18 |
| resistance_band | 18 |
| cable | 13 |
| dumbbell | 11 |
| dumbbell+adjustable_bench | 7 |
| pull_up_bar | 5 |
| exercise_ball | 5 |
| treadmill | 5 |
| bodyweight+resistance_band | 3 |
| barbell+plates | 3 |
| barbell+rack+plates | 3 |
| ez_bar+plates | 3 |

### Primary unresolved causes

| Primary unresolved cause | Visual identities |
| --- | --- |
| no_semantic_candidate | 32 |
| insufficient_exactness_evidence | 21 |
| movement_path_range_or_execution | 16 |
| body_position_or_support | 14 |
| laterality_grip_stance_or_load | 13 |
| equipment_or_attachment | 6 |

Highest-value Visualization v2 work is the unresolved band/cable accessory cluster, stability-ball core and hamstring work, distinct treadmill protocol visuals, loaded carries/marches, and setup-sensitive dumbbell/barbell variants. These gaps need either a provider with richer physical-variant metadata/media, provider clarification plus deeper manual review, or future repository-owned assets. The 25 prior provider catalog-expansion candidates remain separate and no canonical exercise was added here.

## Licensing and provider-policy recheck

Official free V1 documentation expressly states:

- allowed: personal projects, prototypes, educational tools, non-commercial apps, and community-driven fitness platforms;
- prohibited without a paid RapidAPI plan: commercial products, SaaS, and monetized use;
- AscendAPI attribution is required;
- free media is limited to one 180p GIF per exercise.

The reviewed official pages do not clearly state permission for permanent local caching, repository vendoring, redistribution, or CDN mirroring. They also do not define a cache duration. Silence is not treated as permission. Remote media use is described as part of permitted free-tier projects, but production/commercial use and durable ingestion require an applicable paid agreement plus explicit written clarification for the planned storage/distribution model.

Therefore the approved semantic slice is ready to hand to a future ingestion design, but production ingestion is blocked on provider rights: `SEMANTICALLY_READY_PROVIDER_RIGHTS_BLOCKED`.

## Evidence and safety

- Matrix: `docs/project_memory/spikes/ascendapi_structured_coverage_reassessment_matrix_v1.csv` — exactly 151 deterministic rows, one per direct-uncovered visual identity.
- No production code or runtime data changed.
- No application startup or browser smoke was required or performed.
- `fitness_ai.db` was never opened, copied, seeded, migrated, or hashed by this spike.
- The provider inventory, NDJSON state, GIFs, contact sheets, and temporary analyzers are closeout-only temporary artifacts and are removed before completion.

## Architecture acceptance

Status: Architecture accepted after direct evidence review, deterministic coverage reconciliation, and provider-rights review.
