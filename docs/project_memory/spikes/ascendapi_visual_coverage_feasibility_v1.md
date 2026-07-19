# AscendAPI Visual Coverage Feasibility v1

Status: spike evidence complete for V1 bulk acquisition; production integration is not authorized by this spike.

## Baseline

- 240 canonical exercises.
- 83 already covered by approved Free Exercise DB media.
- 157 analyzed for AscendAPI V1 gap filling.

## V1 acquisition and results

The official free hosted V1 inventory was acquired once using 60 pages of 25 records with documented `after` cursor pagination. Accessible inventory: 1,500 exercises. Candidate generation and ranking then ran locally against the temporary metadata cache; no per-exercise remote searches were used.

- Exact matches: 12 / 157 (7.6% of uncovered gaps; projected total catalog coverage: 95 / 240, or 39.6%).
- Review candidates: 107.
- No matches: 38.
- V2: NOT RUN — `ASCENDAPI_RAPIDAPI_KEY` was not available.

The exact bucket is intentionally conservative. Text/equipment ranking generated candidates, but exact approval also required variant compatibility and representative GIF review. Ambiguous or variant-sensitive results remain review candidates.

## Exact canonical-to-provider mappings

| Canonical exercise | Provider ID | Provider name | Equipment | Media | Reference | Review note |
| --- | --- | --- | --- | --- | --- | --- |
| Cable Lat Pulldown | `qdRxqCj` | cable pulldown (pro lat bar) | cable | GIF | https://static.exercisedb.dev/media/qdRxqCj.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Dumbbell Rear Delt Fly | `8DiFDVA` | dumbbell rear fly | dumbbell | GIF | https://static.exercisedb.dev/media/8DiFDVA.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Dumbbell Hammer Curl | `slDvUAU` | dumbbell hammer curl | dumbbell | GIF | https://static.exercisedb.dev/media/slDvUAU.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Neutral-Grip Pull-Up | `0V2YQjW` | pull up (neutral grip) | body weight | GIF | https://static.exercisedb.dev/media/0V2YQjW.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Hanging Oblique Knee Raise | `BaE7O6U` | hanging oblique knee raise | body weight | GIF | https://static.exercisedb.dev/media/BaE7O6U.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Band Biceps Curl | `3omWx6P` | band alternating biceps curl | band | GIF | https://static.exercisedb.dev/media/3omWx6P.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Band Shoulder Press | `peAeMR3` | band shoulder press | band | GIF | https://static.exercisedb.dev/media/peAeMR3.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Band Pull-Through | `VtTbiP3` | band pull through | band | GIF | https://static.exercisedb.dev/media/VtTbiP3.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Band Pallof Press | `9pa4H5m` | band horizontal pallof press | band | GIF | https://static.exercisedb.dev/media/9pa4H5m.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Cable Upright Row | `cALKspW` | cable upright row | cable | GIF | https://static.exercisedb.dev/media/cALKspW.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Cable Lateral Raise | `goJ6ezq` | cable lateral raise | cable | GIF | https://static.exercisedb.dev/media/goJ6ezq.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |
| Dumbbell Cross-Body Hammer Curl | `Qyk5J3p` | dumbbell cross body hammer curl | dumbbell | GIF | https://static.exercisedb.dev/media/Qyk5J3p.gif | Conservative exact semantic match; representative V1 GIF review supported the movement family. |

## Review candidates

Dumbbell Shoulder Press; Chest-Supported Dumbbell Row; Dumbbell RDL; Hanging Knee Raise; Push Press; Band Face Pull; Band Row; Band Triceps Pressdown; Cable Row; Lat Pulldown; Machine Row; Bike Steady State; Bike Intervals; Dumbbell Pullover; Dumbbell Skull Crusher; Dumbbell Lateral Lunge; Dumbbell Bulgarian Split Squat; Dumbbell Sumo Squat; Dumbbell Front Squat; Dumbbell Single-Leg RDL; Dumbbell Hip Thrust; Dumbbell Front Rack Carry; Dumbbell Calf Raise; Barbell Reverse Lunge; Barbell Split Squat; Barbell High Pull; Band Hammer Curl; Band Overhead Triceps Extension; Band Lateral Raise; Band Lat Pulldown; Band Straight-Arm Pulldown; Band Resisted Push-Up; Band Woodchop; Band Lateral Walk; Band Monster Walk; Band Glute Bridge; Single-Arm Cable Row; Cable High Row; Cable Reverse Fly; Cable Chest Fly; Single-Arm Cable Press; Cable Y Raise; Cable External Rotation; Cable Pull-Through; Cable Pallof Press; Rope Face Pull; Stability Ball Hamstring Curl; Stability Ball Rollout; Stability Ball Plank; Stability Ball Stir-the-Pot; Stability Ball Wall Squat; Stability Ball Dead Bug; Bike Recovery Ride; Bike Hill Intervals.; Cable Woodchop; Bear Crawl; Wall Sit; Pike Push-Up; Close-Grip Push-Up; Plate Front Raise; EZ-Bar Reverse Curl; EZ-Bar Preacher-Style Curl; EZ-Bar Overhead Triceps Extension; EZ-Bar Upright Row; Wall Push-Up; Scapular Push-Up; Plank Shoulder Tap; Side Plank Reach-Through; Half-Kneeling Hip Flexor Stretch; Child's Pose Lat Stretch; Dumbbell Squeeze Press; Low-Incline Dumbbell Press; Dumbbell Tate Press; Dumbbell Reverse Curl; Dumbbell Spider Curl; Dumbbell Suitcase Deadlift; Dumbbell Farmer March; Dumbbell Suitcase March; Dumbbell Tempo Goblet Squat; Dumbbell Heel-Elevated Goblet Squat; Dumbbell Offset Reverse Lunge; Dumbbell Skater Squat; Dumbbell Renegade Row; Barbell Calf Raise; Barbell Hip Hinge Drill; Barbell Tall-Kneeling Press; Barbell Reverse-Grip Row; EZ-Bar Close-Grip Floor Press; EZ-Bar JM Press; Pull-Up Bar Dead Hang; Band Chest Press; Band Squat; Band Split Squat; Band Romanian Deadlift; Band Hamstring Curl; Band Dead Bug Pulldown; Band Anti-Rotation Hold; Band Shoulder Dislocate; Cable Rear Delt Row; Cable 90/90 External Rotation; Cable Lateral Lunge; Cable Romanian Deadlift; Cable Kickback; Cable Anti-Rotation Hold; Rope Cable Curl; Bike Easy Spin; Bike Cadence Drill..

## Remaining no-match gaps

Reverse Lunge; Chest-Supported Row; Back Squat; Treadmill Incline Walk; Treadmill Intervals; Chest-Supported Rear Delt Fly; Suitcase Carry; Waiter Carry; Pendlay Row; Negative Pull-Up; Commando Pull-Up; Dead Hang; Rope Hammer Curl; Treadmill Easy Jog; Treadmill Hill Intervals; Treadmill Tempo Run; Bike Tempo Ride; Bird Dog; Hollow Body Hold; Hollow Rock; Lateral Lunge; Tempo Push-Up; Pause Squat; Plate Curl; Plate Pinch Carry; Heel Tap; Seated Knee Tuck; Toe Walk; Heel Walk; Prone Y-T-W Raise; Cat-Cow; Quadruped T-Spine Rotation; 90/90 Hip Switch; Wall Slide; EZ-Bar Drag Curl; Pull-Up Flexed-Arm Hang; Treadmill Recovery Walk; Treadmill Easy Intervals.

## Media-quality findings

- V1 provides one 180p GIF per exercise; the bulk payload also includes body parts, target/secondary muscles, equipment, and instructions.
- Representative GIF review found useful, legible demonstrations for cable pulldown, dumbbell hammer curl, and cable lateral raise families.
- At least one name-ranked candidate was semantically misleading: the provider GIF returned for Dumbbell Tate Press showed a generic dumbbell press, so it was rejected from exact coverage.
- Other variant-sensitive results (body position, unilateral/bilateral execution, incline/decline, and exact grip) remain review candidates rather than counted coverage.
- No watermark was observed in the representative V1 GIFs; the official documentation limits free V1 media to 180p GIFs.

## Licensing and usage-policy findings

### Confirmed

- Official V1 documentation permits personal projects, prototypes, educational tools, non-commercial apps, and community-driven fitness platforms.
- AscendAPI attribution is required.
- Commercial products, SaaS, and monetized use require a paid RapidAPI plan.
- Free V1 media is limited to 180p GIFs.

### Unclear / requires provider clarification

- The official free V1 documentation does not clearly grant permanent local caching or repository redistribution rights for GIF media.
- Permanent vendoring, cache duration, CDN mirroring, and commercial/SaaS upgrade terms require explicit provider clarification before production ingestion.

## Provider architecture recommendation

Recommendation: MORE EVIDENCE REQUIRED before production integration. If AscendAPI confirms caching/redistribution rights, an ingestion/cache pipeline is the best fit: backend-controlled, provenance-preserving, checksum-verified, and independent of runtime provider availability. Until then, preserve the existing local Free Exercise DB projection and do not add remote runtime calls or vendored AscendAPI media.

## High-value future canonical catalog-expansion candidates

| Provider name | Provider ID | Why it fills a meaningful gap | Equipment | Media |
| --- | --- | --- | --- | --- |
| kettlebell swing | `UHJlbu3` | Practical kettlebell hinge/conditioning staple. | kettlebell | GIF |
| kettlebell turkish get up (squat style) | `Ha7SZ3y` | High-value full-body kettlebell skill. | kettlebell | GIF |
| kettlebell pistol squat | `5bpPTHv` | Useful unilateral lower-body progression. | kettlebell | GIF |
| kettlebell arnold press | `UM8mgyG` | Accessible kettlebell shoulder-press variant. | kettlebell | GIF |
| kettlebell thruster | `yWxMvB5` | Common power/conditioning movement. | kettlebell | GIF |
| kettlebell two arm clean | `7Ba7bQ2` | Foundational kettlebell clean. | kettlebell | GIF |
| kettlebell one arm snatch | `aXcUyKb` | Common overhead power movement. | kettlebell | GIF |
| smith low bar squat | `RGLscZM` | Smith-machine squat for commercial gyms. | smith machine | GIF |
| smith bench press | `trqKQv2` | Smith-machine horizontal push alternative. | smith machine | GIF |
| smith single leg split squat | `wWFspEi` | Machine-assisted unilateral squat progression. | smith machine | GIF |
| cable seated row | `fUBheHs` | Common cable row variant. | cable | GIF |
| cable rope seated row | `SJqRxOt` | Cable seated row with rope attachment. | cable | GIF |
| cable kneeling rear delt row (with rope) (male) expanded | `eZ79rbI` | Cable rear-delt/prehab variation. | cable | GIF |
| cable pull through (with rope) | `OM46QHm` | Cable glute/hinge accessory. | cable | GIF |
| cable standing shoulder external rotation | `FWdVhcW` | Useful rotator-cuff/prehab movement. | cable | GIF |
| cable kickback | `HEJ6DIX` | Common cable glute kickback. | cable | GIF |
| exercise ball hip flexor stretch | `2LQkNPW` | Beginner-friendly hip-flexor mobility. | stability ball | GIF |
| world greatest stretch | `DFGXwZr` | High-value whole-body mobility drill. | body weight | GIF |
| calf stretch with hands against wall | `m0tCHqc` | Simple calf mobility regression. | body weight | GIF |
| kneeling lat stretch | `f38OEuO` | Practical lat mobility variation. | body weight | GIF |
| runners stretch | `0mB6wHO` | Common running warm-up mobility. | body weight | GIF |
| cable seated chest press | `nIR4Rwl` | Cable chest-press alternative. | cable | GIF |
| cable lateral pulldown (with rope attachment) | `CuaWCmC` | Rope cable lat-pulldown variation. | cable | GIF |
| cable kneeling rear delt row (with rope) (male) | `G61cXLk` | Cable rear-delt row with rope. | cable | GIF |
| cable rear delt row (with rope) | `wqNPGCg` | Cable rear-delt row variation. | cable | GIF |

## Validation and safety

- Local analyzer evaluated all 157 uncovered canonical names against the cached 1,500-record inventory.
- Representative visual review used six temporary GIF downloads; all were removed after review.
- No database access or mutation occurred; `fitness_ai.db` was untouched.
- No frontend validation, browser smoke, or full test suite was run, per spike authorization.
- Temporary provider cache and scripts are removed during closeout.
