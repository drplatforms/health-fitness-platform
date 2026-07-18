# Visual Exercise Form Guidance v1

Status: Architecture accepted; pending Git closeout.

Baseline: `main @ 388c326` (`Merge injury temporary limitation mode v1`).

Feature branch: `feature/visual-exercise-form-guidance-v1`.

## Implemented boundary

- Canonical `exercise_catalog_exercises.id` owns each runtime media record.
- `exercise_catalog_form_media` is an additive metadata projection with composite `(exercise_id, media_key)` identity and a foreign key to the canonical catalog.
- Only approved, checksum-verified local `static_image` assets under `/exercise-media/free-exercise-db/` are served at runtime.
- Existing repository-owned instruction content remains authoritative. Form media supplements it through the existing instruction response as `form_media`.
- No remote runtime loading, source dependency, provider imagery, generated imagery, video, workout-engine behavior, ranking, substitutions, progression, or planner behavior was added.

## Authorized source and provenance

The approved local media library vendors images from [Free Exercise DB](https://github.com/yuhonas/free-exercise-db), whose repository declares the [Unlicense](https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md). Each persisted media row records source name, source exercise ID, source raw-asset URL, license name/URL, local public path, and SHA-256. Startup uses no network access.

## Initial starter mapping

The initial reviewed starter slice contained 12 canonical exercises and 24 static images:

| Canonical exercise | Free Exercise DB source ID |
| --- | --- |
| Incline Push-Up | `Incline_Push-Up` |
| Bodyweight Squat | `Bodyweight_Squat` |
| Plank | `Plank` |
| Dead Bug | `Dead_Bug` |
| Inverted Row | `Inverted_Row` |
| Dumbbell Bench Press | `Dumbbell_Bench_Press` |
| Seated Dumbbell Shoulder Press | `Dumbbell_Shoulder_Press` |
| One-Arm Dumbbell Row | `One-Arm_Dumbbell_Row` |
| Goblet Squat | `Goblet_Squat` |
| Barbell Squat | `Barbell_Squat` |
| Romanian Deadlift | `Romanian_Deadlift` |
| Barbell Curl | `Barbell_Curl` |

Each mapping has ordered `Start` and `Finish` local images. Uncovered catalog exercises return `form_media: []` and keep the existing text-only instruction experience.

## User experience

`ExerciseInstructionDisclosure` renders a compact responsive two-image Visual guide only when approved form media is present. For unfamiliar or learning exercises, the guide is placed before the overview; for familiar or unset exercises, it follows the overview. The existing Learn, Review, and How To affordances, disclosure behavior, text instructions, profile editing, and workout-state isolation remain unchanged.

## Architecture acceptance

Architecture accepted Visual Exercise Form Guidance v1 on 2026-07-18 at `83` covered canonical exercises and `166` approved local static images. The full `240`-exercise catalog is classified into `83` covered, `81` rejected material-variant candidates, and `76` no-source-match exercises. The remaining `157` exercises are explicit future provider-coverage inputs rather than unclassified gaps.

Acceptance used targeted, risk-based validation appropriate to the implementation and coverage-expansion blast radius. The full repository suite was intentionally not rerun; milestone closeout alone is not a reason to run it.

## Validation evidence

- Gate 0 removed the rejected `Hanging Knee Raise -> Bent-Knee_Hip_Raise` mapping and both vendored images. No approximate substitute was added.
- Final exact-match sweep: `83` covered canonical exercises and `166` ordered local images; `157` remain uncovered (`81` rejected material-variant candidates and `76` with no sufficiently equivalent source match).
- Focused catalog, instruction, form-media persistence/seed, and API tests: `79 passed`.
- Exact-projection reconciliation and rollback tests passed using temporary databases only; the projection remains transactional, checksum-verified, provenance-complete, and text-only for uncovered exercises.
- Targeted Ruff check and format check: passed.
- Frontend `npm run lint` and `npm run build`: passed.
- Project-memory tests: `29 passed`; checker: `PASS=609 WARN=38 FAIL=0` with pre-existing stale-documentation warnings.
- The full repository pytest suite was intentionally not rerun under the corrected targeted-validation policy.
- Architecture-authorized cleanup removed only the feature-owned `exercise_catalog_form_media` projection after read-only confirmation of its `24` rows, no foreign-key/reference dependency, stopped canonical writers, no listeners on ports `8000`/`3100`, and `PRAGMA quick_check = ok`. The controlled cleanup record is: “Feature-owned form-media projection was reintroduced while live feature-branch application writers were connected to the canonical database. Exact table removed after read-only forensic confirmation. Historical writer attribution remains unresolved, but the prior 12/24 projection indicates live startup seeding is the leading explanation.”
- With canonical writers stopped, the fresh post-cleanup SHA-256 baseline and post-validation hash were exactly equal: `adf3a7e2f45a32454e8029060f5b35667e9ed2a632a71756a55820947dfdd395`.
- Production browser smoke passed against a disposable physical database copy: the workout page loaded, `Barbell Squat` opened its local Visual guide with Start/Finish images and instructions, and browser console errors were empty. The disposable database, launcher, logs, and listeners were removed. Canonical remained disconnected and hash-identical.
- `git diff --check` passed. No full-suite rerun, staging, commit, push, merge, snapshot, or self-acceptance occurred.

## Final three-bucket catalog sweep

The canonical catalog contains `240` exercises. The repository manifest is the authoritative COVERED list; every name below is canonical and appears in exactly one bucket.

### COVERED — 83 exact source matches

Incline Push-Up; Bodyweight Squat; Plank; Dead Bug; Inverted Row; Dumbbell Bench Press; Seated Dumbbell Shoulder Press; One-Arm Dumbbell Row; Goblet Squat; Barbell Squat; Romanian Deadlift; Barbell Curl; Split Squat; Glute Bridge; Side Plank; Mountain Climber; Incline Dumbbell Press; Dumbbell Row; Dumbbell Split Squat; Dumbbell Reverse Lunge; Dumbbell Lateral Raise; Dumbbell Curl; Dumbbell Triceps Extension; Farmer Carry; Front Squat; Barbell Bench Press; Overhead Press; Barbell Row; Conventional Deadlift; Hip Thrust; EZ-Bar Skull Crusher; EZ-Bar Close-Grip Press; Band-Assisted Pull-Up; Band Pull-Apart; Band External Rotation; Cable Face Pull; Cable Triceps Pressdown; Cable Curl; Machine Chest Press; Treadmill Walk; Superman Hold; Walking Lunge; Standing Calf Raise; Single-Leg Glute Bridge; Dumbbell Floor Press; Dumbbell Fly; Incline Dumbbell Fly; Arnold Press; Dumbbell Front Raise; Dumbbell Shrug; Dumbbell Upright Row; Dumbbell Concentration Curl; Dumbbell Zottman Curl; Dumbbell Kickback; Dumbbell Close-Grip Press; Dumbbell Step-Up; Box Squat; Barbell Good Morning; Barbell Floor Press; Close-Grip Bench Press; Incline Barbell Bench Press; Barbell Rollout; Hanging Leg Raise; Cable Crunch; Reverse Crunch; Cable Chest Press; Rope Triceps Pressdown; Rope Overhead Triceps Extension; Straight-Arm Cable Pulldown; Push-Up; Pull-Up; Bench Dip; Rack Pull; EZ-Bar Curl; Chin-Up; Decline Push-Up; Barbell Glute Bridge; Scapular Pull-Up; Band Good Morning; Cable Internal Rotation; Barbell Shrug; Barbell Lunge; Leg Press.

### NOT COVERED — REJECTED — 81 material-variant candidates

Reverse Lunge; Dumbbell Shoulder Press; Chest-Supported Dumbbell Row; Chest-Supported Row; Dumbbell RDL; Back Squat; Hanging Knee Raise; Push Press; Band Face Pull; Band Row; Band Triceps Pressdown; Cable Row; Cable Lat Pulldown; Lat Pulldown; Machine Row; Treadmill Incline Walk; Treadmill Intervals; Bike Steady State; Bike Intervals; Dumbbell Pullover; Dumbbell Rear Delt Fly; Chest-Supported Rear Delt Fly; Dumbbell Hammer Curl; Dumbbell Skull Crusher; Dumbbell Lateral Lunge; Dumbbell Bulgarian Split Squat; Dumbbell Sumo Squat; Dumbbell Front Squat; Dumbbell Single-Leg RDL; Dumbbell Hip Thrust; Suitcase Carry; Waiter Carry; Dumbbell Front Rack Carry; Dumbbell Calf Raise; Barbell Reverse Lunge; Barbell Split Squat; Pendlay Row; Barbell High Pull; Neutral-Grip Pull-Up; Negative Pull-Up; Commando Pull-Up; Dead Hang; Hanging Oblique Knee Raise; Band Biceps Curl; Band Hammer Curl; Band Overhead Triceps Extension; Band Lateral Raise; Band Shoulder Press; Band Lat Pulldown; Band Straight-Arm Pulldown; Band Pull-Through; Band Resisted Push-Up; Band Pallof Press; Band Woodchop; Band Lateral Walk; Band Monster Walk; Band Glute Bridge; Single-Arm Cable Row; Cable High Row; Cable Reverse Fly; Cable Chest Fly; Single-Arm Cable Press; Cable Upright Row; Cable Y Raise; Cable External Rotation; Cable Pull-Through; Cable Pallof Press; Rope Hammer Curl; Rope Face Pull; Stability Ball Hamstring Curl; Stability Ball Rollout; Stability Ball Plank; Stability Ball Stir-the-Pot; Stability Ball Wall Squat; Stability Ball Dead Bug; Treadmill Easy Jog; Treadmill Hill Intervals; Treadmill Tempo Run; Bike Recovery Ride; Bike Tempo Ride; Bike Hill Intervals.

These candidates have a plausible related source but fail exact equipment, body position, stance, unilateral/bilateral execution, grip, incline, machine/free-weight, or named-variant requirements. In particular, `Hanging Knee Raise -> Bent-Knee_Hip_Raise` is rejected because the vendored source is a supine floor movement, not a hanging movement. Push Press: Exact exercise source exists, but the available static image pair does not depict the defining overhead press phase sufficiently for approved form guidance.

### NOT COVERED — NO SOURCE MATCH — 76

Cable Lateral Raise; Cable Woodchop; Bear Crawl; Bird Dog; Hollow Body Hold; Hollow Rock; Lateral Lunge; Wall Sit; Pike Push-Up; Close-Grip Push-Up; Tempo Push-Up; Pause Squat; Plate Front Raise; Plate Curl; Plate Pinch Carry; EZ-Bar Reverse Curl; EZ-Bar Preacher-Style Curl; EZ-Bar Overhead Triceps Extension; EZ-Bar Upright Row; Wall Push-Up; Scapular Push-Up; Plank Shoulder Tap; Heel Tap; Side Plank Reach-Through; Seated Knee Tuck; Toe Walk; Heel Walk; Prone Y-T-W Raise; Cat-Cow; Quadruped T-Spine Rotation; Half-Kneeling Hip Flexor Stretch; 90/90 Hip Switch; Child's Pose Lat Stretch; Wall Slide; Dumbbell Squeeze Press; Low-Incline Dumbbell Press; Dumbbell Tate Press; Dumbbell Reverse Curl; Dumbbell Cross-Body Hammer Curl; Dumbbell Spider Curl; Dumbbell Suitcase Deadlift; Dumbbell Farmer March; Dumbbell Suitcase March; Dumbbell Tempo Goblet Squat; Dumbbell Heel-Elevated Goblet Squat; Dumbbell Offset Reverse Lunge; Dumbbell Skater Squat; Dumbbell Renegade Row; Barbell Calf Raise; Barbell Hip Hinge Drill; Barbell Tall-Kneeling Press; Barbell Reverse-Grip Row; EZ-Bar Drag Curl; EZ-Bar Close-Grip Floor Press; EZ-Bar JM Press; Pull-Up Bar Dead Hang; Pull-Up Flexed-Arm Hang; Band Chest Press; Band Squat; Band Split Squat; Band Romanian Deadlift; Band Hamstring Curl; Band Dead Bug Pulldown; Band Anti-Rotation Hold; Band Shoulder Dislocate; Cable Rear Delt Row; Cable 90/90 External Rotation; Cable Lateral Lunge; Cable Romanian Deadlift; Cable Kickback; Cable Anti-Rotation Hold; Rope Cable Curl; Treadmill Recovery Walk; Treadmill Easy Intervals; Bike Easy Spin; Bike Cadence Drill.

No mapping was forced for either uncovered bucket. The architecture remains local static images, a repository-owned manifest, an exact transactional runtime projection, SHA-256/provenance validation, and text-only fallback.
