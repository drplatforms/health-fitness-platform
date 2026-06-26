# Current State

Latest accepted milestone: Exercise Eligibility Matrix v1.

Latest accepted feature commit: `851a7ca`.

Latest main merge commit: `f469c89`.

Latest accepted snapshot: `fitness_ai_snapshot_2026-06-26_851a7ca_update-exercise-eligibility-matrix-project-memory.zip`.

Current planning milestone: Nutrition Catalog + Serving Foundation Planning v1.

Current branch: `feature/nutrition-catalog-serving-foundation-planning-v1`.

Source baseline: `main` at `f469c89`.

Milestone type: planning / architecture / project memory only.

## Current process doctrine

The current operating doctrine is:

> Bite by bite, just bigger bites.

Meaning:

- Larger objectives are allowed.
- Single patches stay narrow.
- Complexity determines process weight.
- Complex backend behavior requires diagnostic-first and test-first gates where practical.
- Real smoke failures become automated regression tests, diagnostic/coverage tests, documented limitations, or backlog items.
- Architecture defines v1/v2 scope before branches spiral.
- Backend must not blindly stack patches after repeated failures.
- QA validates the real user path, not only generic test-green status.

## Recent accepted milestones

### Workout Preview Full-Slot Rotation v1

Accepted and merged.

- Feature commit: `3b32f97`
- Main merge commit: `f39b403`
- Snapshot: `fitness_ai_snapshot_2026-06-25_3b32f97_fix-first-refresh-workout-slot-rotation.zip`
- Accepted scope: immediate previous-preview anti-repeat.
- Deferred v2 scope: rolling multi-refresh novelty.

This milestone proved that generic tests were not enough. The real path was `variation 0 -> variation 1`, where refreshed previews repeated exercises despite valid alternatives. A focused quality gate reproduced the behavior before the narrow fix landed.

### Exercise Catalog Utilization / Specialized Movement Coverage v1

Accepted and merged.

- Feature commit: `1d44b3d`
- Main merge commit: `b343a47`
- Snapshot: `fitness_ai_snapshot_2026-06-26_1d44b3d_preserve-primary-workout-rotation-after-catalog-expansion.zip`
- Accepted scope: improved deterministic catalog breadth and specialized movement reachability past quality gates.
- Preserved: Quick / Standard / Full sizing, immediate preview refresh anti-repeat, selected workout persistence, Active Workout persistence, Today workout de-dup, and no provider/AI workout generation path.
- Deferred future scope: Exercise Eligibility Matrix v1, Catalog Reachability Audit v2, rolling exposure tracking, deeper movement-family de-duplication, and complete catalog reachability.

This milestone proved the value of stop conditions. The first breadth implementation improved utilization but regressed preview rotation. Linux smoke later caught a home-gym hinge/vertical_pull regression. Patch drift also occurred. The final accepted branch succeeded only after each failure was treated as a diagnostic signal instead of continuing blind patch stacking.

### Test-First Quality Gate Development Plan v1

Accepted and merged.

- Feature commit: `227990e`
- Main merge commit: `37d210f`
- Snapshot: `fitness_ai_snapshot_2026-06-26_227990e_clarify-continuity-brief-metadata.zip`
- Accepted scope: canonized diagnostic-first / test-first quality gate process.
- Preserved: no app/runtime behavior changes, no service changes, no provider changes, no workout/nutrition/catalog behavior changes.

This milestone made the current quality doctrine repo-discoverable instead of chat-only.

### Exercise Eligibility Matrix v1

Accepted and merged.

- Feature commit: `851a7ca`
- Primary code checkpoint commit: `05d319e`
- Main merge commit: `f469c89`
- Snapshot: `fitness_ai_snapshot_2026-06-26_851a7ca_update-exercise-eligibility-matrix-project-memory.zip`
- Accepted scope: explicit generator-facing exercise eligibility matrix, diagnostic tool, quality-gate tests, reachability/exclusion visibility, and preserved workout behavior.
- Preserved: Quick / Standard / Full sizing, immediate preview refresh anti-repeat, selected workout persistence, Active Workout persistence, Today workout de-dup, no provider/AI workout generation path.
- Deferred future scope: complete catalog reachability, rolling multi-refresh novelty, persistent exercise exposure tracking, arms/mobility slot expansion, deeper movement-family de-duplication, and optional diagnostic/service deduplication cleanup.

Diagnostic baseline from the accepted branch:

- total active catalog exercises: 240
- equipment-compatible exercises: 237
- generator-eligible exercises classified by matrix/diagnostic: 232
- exercises selected in 10-variation deterministic sweep: 54
- largest exclusion reason: `not_supported_by_current_generator_candidate_pools` (170)
- weak movement families called out by diagnostic: arms_biceps, arms_triceps, mobility

## Current planning milestone

Nutrition Catalog + Serving Foundation Planning v1 is authorized as a planning / architecture / project-memory-only milestone.

The purpose is to define the nutrition backend foundation sequence before implementation begins. Upcoming nutrition features are connected enough that the project needs a clear architecture path before changing code:

- food catalog expansion
- canonical food curation
- serving-size conversion to grams
- household measures
- nutrition actuals confidence
- deterministic food suggestions
- later AI meal/snack candidate generation

This milestone does not authorize implementation of catalog expansion, serving units, food logging changes, provider behavior, Streamlit UI changes, database migrations, workout work, or recovery work.

## Nutrition foundation direction

Nutrition should become a grounded coaching engine, not only a calorie/macro logger.

Backend owns:

- food truth
- canonical foods
- nutrient data
- serving unit conversions
- grams
- confidence
- logged actuals
- targets
- gaps
- validation
- fallback

Provider/AI may eventually help explain or assemble approved facts, but must not invent foods, macros, serving sizes, gram conversions, targets, missing intake, or health claims.

## Two-layer food catalog strategy

Future nutrition work should strongly prefer a two-layer model.

Layer 1: raw / source food data.

- large imported food datasets
- USDA or source records
- not directly user-facing
- useful for search, enrichment, mapping, future expansion

Layer 2: canonical app food catalog.

- curated food names
- aliases
- nutrients per 100g
- approved serving units
- confidence/source metadata
- safe for logging
- safe for deterministic suggestions
- safe for AI/provider contracts

Doctrine: do not expose a huge raw import directly to food logging, suggestions, or provider contracts. Raw/staging imports can be large, but only approved canonical foods should power normal user-facing flows.

## Serving unit / confidence strategy

The backend should support weighed grams when precision matters and practical serving units when convenience matters.

Examples:

- `180g cooked white rice`
- `1/2 cup cooked white rice`
- `1 medium banana`
- `1 large egg`
- `1 tbsp peanut butter`
- `1 scoop protein powder`
- `1 slice bread`
- `1 cup Greek yogurt`

Approved serving units should convert to grams using validated metadata with default grams, optional min/max range, confidence, source, and source notes.

Important rule: do not pretend household measures are exact. Store a default grams value, a range where useful, and a confidence level.

## Recommended nutrition roadmap

Recommended sequence after this planning milestone:

1. Nutrition Catalog Diagnostic v1.
2. Nutrition Canonical Food Model Review v1.
3. Curated Food Catalog Expansion v1.
4. Serving Unit Normalization / Household Measure Conversion v1.
5. Nutrition Logging Backend Contract v1.
6. Nutrition Actuals Confidence v1.
7. Nutrition Deterministic Food Suggestions v1.
8. Nutrition AI Meal/Snack Candidate Contract v1.

Recommended next implementation milestone: Nutrition Catalog Diagnostic v1.

## Complex Backend Quality Gate

For any complex feature involving state, scoring, selection, persistence, provider output, routing, nutrition targets, workout generation, recommendation logic, or user-visible workflow behavior:

1. Diagnose current behavior before patching.
2. Identify the exact failing, missing, or underperforming user path.
3. Add a failing regression test, diagnostic test, or coverage test that captures the real path where practical.
4. Confirm the test fails or exposes the gap before implementation.
5. Apply the smallest safe implementation change.
6. Prove the new test passes.
7. Re-run prior milestone regression tests.
8. Re-run the original manual/browser smoke path.
9. Update project memory.
10. Only then request Architecture acceptance.

Do not treat generic green tests as sufficient if the product-critical path is not covered.

## Current boundaries

- Deterministic backend owns truth.
- Provider may propose only inside approved contracts.
- Backend validates and approves.
- User sees only approved output.
- Deterministic fallback remains mandatory.
- No provider may run on normal Today page load unless Architecture explicitly promotes it.
- No provider/AI workout generation is accepted.
- No provider may invent foods, serving units, grams, macros, targets, or gaps.
- No raw/staging food import should directly power user-facing logging, suggestions, or provider contracts.
- No CrewAI/Ollama/OpenAI/PydanticAI/LangGraph workout generation is accepted.
- No worker/queue/scheduler/polling is accepted unless explicitly scoped.
- No broad rewrite is authorized by process docs.
- Codex is not used by default.
- Nutrition Catalog + Serving Foundation Planning v1 is docs/project-memory only.

## Current next-roadmap candidates

After Nutrition Catalog + Serving Foundation Planning v1 is accepted, likely roadmap candidates are:

- Nutrition Catalog Diagnostic v1.
- Nutrition Canonical Food Model Review v1.
- Curated Food Catalog Expansion v1.
- Serving Unit Normalization / Household Measure Conversion v1.
- Nutrition Logging Backend Contract v1.
- Nutrition Actuals Confidence v1.
- Nutrition Deterministic Food Suggestions v1.
- Nutrition AI Meal/Snack Candidate Contract v1.
- Catalog Reachability Audit v2 later.
- Workout Preview Rolling Exposure Rotation v2 later.
- Recovery engine improvements later.

## Historical continuity reminders

Historical project-memory entries remain valid context and should not be erased just because the current active milestone changed:

- Project Memory Alignment + North Star Architecture v1.
- `feature/daily-coach-narrative-same-session-approved-preview-bridge-v1` is reference-only, not accepted.
- Provider Narrative QA Matrix v2.
- Daily Coach Same-Session Approved Preview Bridge v1 Retry.
- Same-Session Bridge Runtime QA v1.
- Daily Coach Narrative Product Voice Polish v1.
- Daily Coach Narrative Product Voice Runtime QA v1.
- PASS_WITH_NOTE product-voice outcomes remain context for future voice work.
- The product goal remains to sound right and be right.
- Local Developer Command Menu Audit + Repo-Owned Commands v1.
- `scripts/fitness_commands.ps1` remains the repo-owned command source.
- Local Command Menu App Runtime Correction v1 clarified that Linux is the canonical app runtime and `wapp` is Windows-local only.
- Daily Coach Async Service Shell / No Worker v1 remains service shell only; no provider execution added.
