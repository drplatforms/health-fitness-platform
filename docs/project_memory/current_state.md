# Current State - Cross-Domain Coaching Synthesis Preview v1

Accepted implementation base: `main` at `9c5ae0f Merge manifest-aware canonical food promotion`.

Current implementation branch:
`feature/cross-domain-coaching-synthesis-preview-v1`.

Status:

```text
READY_FOR_ARCHITECTURE_SEMANTIC_CONTRACT_REVIEW
```

Implementation summary:

- Manifest-aware canonical food promotion is merged; live USDA promotion remains deferred and USDA work is frozen while product coaching work resumes.
- This is an isolated developer-only backend/CLI preview, not a Today-page, public API, normal provider runtime, persistence, schema, migration, or provider-promotion feature.
- Existing Daily Coach snapshot, raw preview payload, synthesis, and approved brief services provide the backend-owned evidence and approved actions. The preview does not query raw database tables directly.
- The complete `CrossDomainEvidencePacket` remains the deterministic audit/provenance source. A separate typed `CrossDomainAssessmentContext` is projected for the specialist call only: recovery/nutrition/training/shared facts are capped at `8/8/10/5` (`31` total), selected through explicit typed-field allowlists, and contain stable evidence ID, domain, semantic fact key, typed value, safe display value, and confidence. Metadata, per-row detail, summaries, coach-safe prose, recommendations, and limitation/source-gap sentences are excluded.
- Provider-facing actions are semantic objects with `action_key`, domain, `action_type`, typed parameters, and source claim keys/support. Recovery maps to `maintain_planned_training`, training maps to `execute_planned_session` with RIR bounds derived from approved claim data, and nutrition maps to `consider_food_candidate` with approved food data and serving permission. Legacy instruction, interpretation, and phrasing prose is neither copied nor parsed. Limitations are semantic conditions and are not selectable actions.
- A successful preview makes at most two provider calls: one strictly parsed structured assessment for recovery, nutrition, and training, then one natural narrative call only after that assessment validates. Assessment and narrative providers/models are independently selected from `mock`, `openai`, and `direct_ollama`; each call has its own injectable developer-test seam.
- Backend remains authoritative for facts, confidence, conditions, scenarios, semantic action availability, deterministic resolution, targets, workout plans, persistence, and fallback. The provider can select approved action keys and write candidate narrative only.
- The assessment response schema is built at runtime from the bounded context. It constrains the assessment version, statuses, confidence, priority permutation, per-domain evidence IDs, specialist-owned action keys, empty-action domains, and tension evidence IDs; the existing strict parser remains mandatory after schema output.
- The narrative call receives a dedicated `cross_domain_semantic_narrative_context_v1` projection rather than the raw `ApprovedCoachBrief`. It contains the resolved semantic decision, typed domain status, bounded relevant approved facts (`6/8/6` by recovery/nutrition/training), semantic confidence conditions, and forbidden-topic codes. It excludes today-intent copy, instruction/interpretation copy, phrasing banks, specialist observations/tension summaries, coach-safe summaries, deterministic fallback prose, and the backend forbidden-certainty phrase list.
- The backend-owned confidence policy and audit retain the certainty phrases internally. Claim audit runs first, confidence-coherence second, and product voice third. Unsupported food, value, serving, timing, causal, certainty, source-gap-denial, and workout-change claims remain rejected without requiring similarity to legacy action sentences.
- The deterministic resolver never restores vetoed actions as primary or supporting actions. Recovery caution alone does not erase backend-approved training actions; only an explicit recovery veto suppresses conflicting training emphasis. Existing claim and product-voice audits decide the developer-preview disposition without repair calls.
- The direct-Ollama adapter uses the existing lifecycle policy, base-URL, model-normalization, and structured `/api/generate` payload conventions. Qwen3 model names receive `think: false` for this strict two-call preview; Qwen2.5 behavior is unchanged. It has no normal-runtime hook or default change.
- Optional artifacts now include the exact prompt-free `semantic_narrative_context.json`; no artifacts are written without `--output-dir`.
- Codex did not run a live provider trial. The semantic-contract focused preview suite passed: `96`; the required focused regression slice passed: `136`. Ruff check and format check passed for all five scoped Python files. Project-memory checker passed with `590 PASS`, `58 WARN`, `0 FAIL`; project-memory tests passed: `29`. No full suite, browser automation, frontend build, provider call, or `fitness_ai.db` access occurred.
- Product-voice audit scoring remains a known follow-up; this correction did not redesign it or weaken any approval audit.
- This preview is not production-ready and does not authorize Today/public/provider promotion.

See milestone memory:
`docs/project_memory/milestones/cross_domain_coaching_synthesis_preview_v1.md`.

---

# Current State - USDA Generic Source-Specific Promotion Rules v0

Current source of truth: `main` at `929886d Merge USDA generic source-specific promotion rules v0`.

Feature implementation commit: `50d7e2b Add USDA source-specific promotion rules`.

Status:

```text
USDA_GENERIC_SOURCE_SPECIFIC_PROMOTION_RULES_V0_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Fixed source precedence is Foundation, SR Legacy, then FNDDS; lower-priority
  collision rows are explicit duplicate-name skips.
- SR Legacy is limited to seven conservative basic-food categories and rejects
  bounded commercial/product-line evidence including Bolthouse Farms, Daily
  Greens, Silk, Vitasoy, and Nasoya, plus USDA distribution-program metadata.
- FNDDS remains fully deferred from canonical promotion.
- Same-name/same-macro families select one deterministic representative; unresolved
  different-macro families no longer use generic comma-phrase renaming.
- Nine initial and 33 review-corrected Foundation display-name mappings, plus a
  peeled-kiwifruit correction, cover the approved diagnostic examples without
  restoring generic comma-phrase fallback.
- SR meatless rows retain their `Meatless` qualifier; soy vermicelli retains its
  soy identity. Focused tests passed: `110`; import/promotion safety tests passed:
  `131`. Ruff check and format check passed.
- Official external dry-runs processed Foundation `469`, SR Legacy `7,793`, FNDDS
  `5,432`, and combined `13,694` rows. Combined promoted `348` rows; all 151
  Foundation-only candidates remained present and reversed data-type order produced
  identical promoted identities and names.
- The final audit found zero promoted Bolthouse/Daily Greens rows, zero promoted
  Silk/Vitasoy/Nasoya rows, zero promoted meatless rows without `Meatless`, zero
  promoted USDA distribution metadata rows, zero `Kiwifruit Kiwi` names, and zero
  adjacent duplicate-word names. General `Kiwifruit` and `Peeled kiwifruit` both
  remain promoted. External evidence verdict:
  `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.
- No canonical records were promoted. Raw count remained `13,694`; canonical
  tables remained empty; the real `fitness_ai.db` was not accessed or mutated.
- The rules remain dry-run evidence only and do not authorize live canonical promotion.
- Accepted merge: `929886d Merge USDA generic source-specific promotion rules v0`.
- Feature implementation: `50d7e2b Add USDA source-specific promotion rules`.
- Project-memory checker passed with `590 PASS`, `58 WARN`, and `0 FAIL`; project-memory tests passed: `29`.
- Final verdict: `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

See milestone memory:
`docs/project_memory/milestones/usda_generic_source_specific_promotion_rules_v0.md`.

---

# Current State - USDA Generic Canonical Promotion Diagnostic v0

Accepted diagnostic base: `main` at `53703aa Close USDA generic full dataset validation memory`.

Status:

```text
USDA_GENERIC_CANONICAL_PROMOTION_DIAGNOSTIC_V0_ACCEPTED_AND_CLOSED
```

Closeout:

- Existing deterministic promotion rules were evaluated against all `13,694` validated generic USDA rows.
- Foundation classified `138` rows as promotable, with `231` duplicate-name skips, `58` unsafe-raw skips, and `42` missing-macro skips.
- SR Legacy classified `670` rows as promotable, with `4,681` duplicate-name skips, `1,274` category skips, `1,166` unsafe-raw skips, and `2` invalid skips.
- FNDDS classified `0` rows as promotable; `5,431` were blocked by current category policy and one lacked supported macros.
- The combined run classified `691` rows as promotable, including `57` Foundation and `634` SR Legacy rows.
- The diagnostic identified `2,534` candidate-name families, `356` multi-source overlaps, `933` same-name families with different macro profiles, and `652` suspicious-name review flags.
- Current combined handling does not preserve Foundation precedence and can allow lower-priority SR Legacy rows to displace Foundation candidates.
- Current generic duplicate renaming can produce malformed commercial or over-generic display names.
- No canonical foods, aliases, nutrients, source links, or raw application rows were changed.
- Final verdict: `READY_FOR_SOURCE_SPECIFIC_PROMOTION_RULE_DESIGN`.
- Existing rules are not approved for live canonical promotion.
- Milestone is accepted and closed. Git is authoritative for the final documentation commit and snapshot hash.

Architecture direction:

- Source precedence will be Foundation, then SR Legacy, then FNDDS.
- Foundation remains the preferred generic source.
- SR Legacy will initially be restricted to conservative basic-food categories, with commercial or manufacturer-style rows rejected.
- FNDDS canonical promotion remains deferred for a separate prepared-food strategy.
- Cross-source collisions will prefer the highest-priority valid source.
- Generic second-phrase renaming will not be used when it creates low-quality names.
- The next source-specific promotion-rules milestone will remain dry-run only.

Retained evidence:

- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\working\usda_generic_promotion_diagnostic_v0.db`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.json`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.md`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_candidate_name_families.csv`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_category_matrix.csv`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_review_samples.csv`

See milestone memory: `docs/project_memory/milestones/usda_generic_canonical_promotion_diagnostic_v0.md`.

---

# Current State - USDA Generic Full-Dataset Validation v0

Accepted validation base: `main` at `fde27bf Close FNDDS macro payload compatibility memory`.

Status:

```text
USDA_GENERIC_FULL_DATASET_VALIDATION_V0_ACCEPTED_AND_CLOSED
```

Closeout:

- The complete official Foundation, SR Legacy, and FNDDS generic datasets imported successfully into one fresh external scratch database.
- Foundation first pass: `469` processed, `469` inserted, `0` updated.
- SR Legacy first pass: `7,793` processed, `7,793` inserted, `0` updated.
- FNDDS first pass: `5,432` processed, `5,432` inserted, `0` updated.
- Total first-pass raw records: `13,694`.
- The full idempotency rerun inserted `0` rows and updated the exact source count for all three datasets.
- Final raw record total remained `13,694`.
- No unexpected source types, duplicate or missing source identities, empty descriptions, negative macro values, or missing resolved categories were found.
- FNDDS provenance was populated for all `5,432` FNDDS records.
- Canonical food and canonical source-link counts remained `0`.
- The real `fitness_ai.db` was not accessed or mutated.
- The repository remained clean and unchanged throughout validation.
- Final verdict: `READY_FOR_GENERIC_CANONICAL_PROMOTION_DIAGNOSTIC`.
- External scratch database and reports were retained for promotion-diagnostic work.
- Milestone is accepted and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Prove that the complete official generic USDA datasets import together, preserve identity and provenance, remain canonical-safe, and rerun idempotently before promotion design begins.
```

Retained evidence:

- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\scratch\usda_generic_full_dataset_validation_v0_final.db`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0_final.json`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0_final.md`

See milestone memory: `docs/project_memory/milestones/usda_generic_full_dataset_validation_v0.md`.

---

# Current State - FNDDS Macro and Payload Compatibility v0.1

Current source of truth: `main` at `21f5655 Merge FNDDS macro and payload compatibility v0.1`.

Feature implementation commit: `9b93a4a Support FNDDS macro identifiers and payload provenance`.

Status:

```text
FNDDS_MACRO_PAYLOAD_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `21f5655 Merge FNDDS macro and payload compatibility v0.1`.
- Feature implementation: `9b93a4a Support FNDDS macro identifiers and payload provenance`.
- Focused importer tests: `48 passed`.
- Importer and bulk-catalog regression: `76 passed`.
- Import and promotion safety regression: `49 passed`.
- Ruff checks and merged-main production browser smoke passed.
- Official full FNDDS import processed `5,432` rows and reran as `0` inserts plus `5,432` updates.
- `5,431` rows preserved all four supported macros; one source row had no supported macros and remained unmodified.
- No schema, migration, canonical promotion, frontend behavior, dependency, or real-database mutation occurred.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Support the nutrient identifier convention used by the current official FNDDS release and preserve resolved WWEIA category descriptions in raw source provenance.
```

Implemented scope:

- Recognized macro definitions are registered through both `nutrient.id` and optional `nutrient.nutrient_nbr` identifiers.
- Existing Foundation and SR Legacy identifier behavior remains supported.
- Conflicting numeric identifier mappings fail clearly; blank optional nutrient numbers remain safe.
- Missing macro source rows remain missing and zero macro values remain zero.
- FNDDS raw payloads now preserve `wweia_food_category_description`.
- The payload description equals the persisted resolved food category.
- The input-only alias key `wweia_food_category` remains excluded from raw payloads.

Validation completed:

- Focused USDA importer tests: `48 passed`.
- USDA importer and bulk-catalog slice: `76 passed`.
- Food import and promotion safety slice: `49 passed`.
- Ruff check and format checks passed for the touched Python files.
- Official full FNDDS first pass: `5,432` processed, `5,432` inserted, `0` updated.
- Official full FNDDS rerun: `5,432` processed, `0` inserted, `5,432` updated.
- `5,431` rows had calories, protein, carbohydrates, and fat; one row had no supported macro values.
- All `5,432` rows preserved food code, WWEIA number, stable WWEIA code, and WWEIA category description.
- There were no duplicates, negative macros, canonical foods, or canonical source links.
- Merged-main production browser smoke passed for Today, Nutrition, canonical search, Workout, console safety, and mobile overflow.
- The real `fitness_ai.db` was not read or mutated.

See milestone memory: `docs/project_memory/milestones/fndds_macro_payload_compatibility_v0_1.md`.

---

# Current State - FNDDS WWEIA Header Compatibility v0.1

Current source of truth: `main` at `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.

Feature implementation commit: `75486d8 Support current FNDDS WWEIA header`.

Status:

```text
FNDDS_WWEIA_HEADER_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.
- Feature implementation: `75486d8 Support current FNDDS WWEIA header`.
- Importer and inventory regression: `70 passed`.
- Import and promotion safety regression: `49 passed`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Ruff checks and production browser smoke passed.
- Official FNDDS 25-row import inserted `25` rows and reran as `0` inserts plus `25` updates.
- No schema, migration, canonical promotion, frontend behavior, or real-database mutation occurred.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Accept the current official FNDDS WWEIA category header without changing generic source selection, promotion, schema, or user-facing behavior.
```

Implemented scope:

- Importer and read-only inventory accept either `wweia_food_category` (current official FNDDS header) or `wweia_food_category_code` (documented/legacy header).
- Both inputs resolve to the stable internal and raw-payload key `wweia_food_category_code`; no `wweia_food_category` payload key is emitted.
- Dual headers accept matching values or one empty value; conflicting non-empty values, missing accepted headers, blank resolved codes, and duplicate resolved codes fail clearly.
- The generic fixture now uses the current official FNDDS header, while focused runtime-copy tests preserve documented and dual-header coverage.
- No schema, migration, source profile, streaming, category semantics, source identity, canonical promotion, CLI, frontend, dependency, or real-database change was added.

Validation completed:

- Importer/inventory regression: `70 passed`.
- Import/promotion safety regression: `49 passed`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Official FNDDS header confirmed as `wweia_food_category,wweia_food_category_description`.
- Official 25-row FNDDS scratch import inserted `25` rows and reran as `0` inserts plus `25` updates; all rows had FNDDS provenance and category descriptions, without duplicates, negative macros, canonical foods, or source links.
- Production browser smoke passed on a temporary database for Today, Nutrition, canonical search, Workout, zero console errors, and no horizontal overflow around 390px.
- Temporary scratch and browser-smoke artifacts and dedicated processes were removed; the real `fitness_ai.db` was not read or mutated.

See milestone memory: `docs/project_memory/milestones/fndds_wweia_header_compatibility_v0_1.md`.

---

# Current State - USDA Generic Source Expansion v0

Current source of truth: `main`. Accepted application merge: `f4b44da Merge USDA generic source expansion v0`.

Latest accepted food-catalog milestone:

```text
USDA Generic Source Expansion v0
```

Status:

```text
USDA_GENERIC_SOURCE_EXPANSION_V0_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `f4b44da Merge USDA generic source expansion v0`.
- Feature implementation: `e8a96ce Expand USDA generic source import`.
- Validation accepted: 58 importer/inventory tests, 44 import/promotion tests, 70 canonical logging/search tests, and 29 project-memory tests.
- Project-memory checker: 590 PASS, 58 WARN, 0 FAIL.
- Production browser smoke passed using a temporary database; the real `fitness_ai.db` was not used or mutated.
- Milestone is merged and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Expand the raw FoodData Central catalog to Foundation Foods, SR Legacy, and Survey Foods (FNDDS) without promoting rows into the canonical catalog.
```

Implemented scope:

- The FDC directory importer defaults to stable keys `foundation_food`, `sr_legacy_food`, and `survey_fndds_food`; branded, experimental, and support rows remain excluded unless explicitly requested.
- `food.csv` and `food_nutrient.csv` are streamed and filtered so only selected foods and their four supported macros are retained in memory.
- FNDDS rows use the documented survey-to-WWEIA category relationship and preserve food code and category provenance in the raw payload.
- Raw records preserve both the original USDA data-type label and its normalized stable key.
- Inventory now reports grouped macro coverage and source-appropriate category counts for all three generic types while remaining read-only.
- Source identity and idempotent upserts remain `source_name + FDC ID`; no canonical promotion, schema, or migration change was added.

Validation completed:

- USDA importer and inventory slice: `58 passed`.
- Food import and promotion regression slice: `44 passed`.
- Canonical logging and search confidence slice: `70 passed`.
- Scratch import processed `5` generic rows (`1` Foundation, `2` SR Legacy, `2` FNDDS), excluded branded/experimental rows, and reran as `5` updates with no duplicates or canonical-table changes.
- Ruff lint/format checks passed for the touched Python files.
- Project-memory validation completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- Read-only production browser smoke passed for Today, Nutrition, canonical food search/logging UI, Workout, zero console errors, and no horizontal overflow around 390px.
- No extracted full local FDC dataset was available for the optional large-dataset validation; no download was attempted.
- The real `fitness_ai.db` was untouched; scratch and browser-smoke artifacts and dedicated processes were removed.

See milestone memory: `docs/project_memory/milestones/usda_generic_source_expansion_v0.md`.

---

# Current State - Workout Execution Integrity Fixes v0.1 (Closed)

Current source of truth: `main` at `d424a83 Merge workout execution integrity fixes v0.1`.

Feature implementation commit: `d2538d7 Fix workout execution integrity`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_d424a83_main_merge-workout-execution-integrity-fixes-v0-1.zip`.

Milestone status:

```text
WORKOUT_EXECUTION_INTEGRITY_FIXES_V0_1_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

The milestone was accepted, merged, pushed, snapshotted, and closed after its targeted tests, Ruff checks, frontend lint/build, project-memory validation, and production browser smoke passed.

See milestone memory: `docs/project_memory/milestones/workout_execution_integrity_fixes_v0_1.md`.

---

# Current State — Agent Workflow Hardening v0 (Closed)

Current source of truth: `main` at `4e89f27 Merge agent workflow hardening v0`.

Accepted merge commit: `4e89f27`.

Feature implementation commit: `1fa45a2`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_4e89f27_main_merge-agent-workflow-hardening-v0.zip`.

Milestone:

```text
Agent Workflow Hardening v0
```

Milestone status:

```text
AGENT_WORKFLOW_HARDENING_V0_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

Purpose:

```text
Add concise repository-native Codex instructions, a reusable milestone loop, a targeted validation matrix, and a read-only status helper without changing application behavior.
```

Delivered scope:

- Replace the historical root instruction bundle with concise repository-wide implementation and safety rules.
- Add frontend-specific instructions for compact UI work and production browser confidence.
- Add the repository-owned `fitness-ai-milestone` skill for implementation and interruption recovery.
- Add a maintainable targeted validation matrix using existing tests only.
- Add a read-only PowerShell milestone status helper with Git, artifact, database, and diff checks.
- Preserve application, API, persistence, dependency, and provider behavior.

Accepted validation:

- Repository skill validation passed.
- The status helper passed normal feature-work inspection and detected a temporary forbidden-artifact fixture without failing; the fixture was removed.
- Independent review hardening confirmed ignored `frontend/.next`, `frontend/node_modules`, nested `tmp/**/__pycache__/*.pyc`, and temporary smoke databases are reported without mutation or a blocking exit; tracked or staged forbidden artifacts remain blocking.
- Final review hardening replaced the recursive `tmp/` scan with a depth-6 walker that skips reparse points and excluded/generated directories; fixtures proved in-depth detection, no `__pycache__` or `node_modules` traversal, no traversal beyond the limit, unchanged files, and exit code `0`.
- Project-memory validation completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- Today/workout persistence, route, and view confidence tests passed with `88 passed`.
- Frontend lint and production build passed.
- Production browser smoke passed against a temporary database copy with zero console errors and no mobile horizontal overflow.
- The real `fitness_ai.db` was not mutated, and milestone-created smoke, bounded-walker fixture, and generated-cache artifacts were removed.
- The milestone was accepted, merged to `main`, pushed, snapshotted, and closed.

See milestone memory: `docs/project_memory/milestones/agent_workflow_hardening_v0.md`.

---

# Current State — Workout Actuals Summary v0

Current source of truth: `feature/workout-actuals-summary-v0`.

Active workout milestone:

```text
Workout Actuals Summary v0
```

Requested status:

```text
WORKOUT_ACTUALS_SUMMARY_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add a compact per-exercise view of logged versus planned workout execution using existing backend-owned planned exercises and actual sets.
```

Implemented scope:

- Added a compact exercise-actuals breakdown below the existing Execution Summary metrics.
- Each planned exercise shows logged/planned set count, accessible set-completion dots, and a neutral completion label.
- Completed non-skipped actual sets determine logged counts; substitution-linked sets remain attributed to their planned exercise.
- Per-exercise average actual RIR maps to hard, moderate, easy, or limited-data effort labels.
- Logged reps map to on-target, mixed, below-range, above-range, or no-logged-reps labels using the planned rep range.
- Extra logged sets remain visible as planned dots plus a neutral extra-set indicator.
- Edits and deletes update the summary through the existing actual-set state and summary refresh paths.

Boundaries preserved:

- No backend route, service, schema, persistence, planned workout snapshot, progression history, completion review, workout generation, recommendation, deload, periodization, nutrition, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Actual set create/edit/delete remains user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Completion remains explicitly user-triggered through the existing completion review and backend completion endpoint.

Validation completed:

- Workout persistence and progression-history slice: `91 passed`.
- Workout planning, route, view, rotation, and sizing slice: `128 passed`.
- Frontend lint and production build passed.
- `git diff --check` passed.
- Browser smoke passed against a temporary database copy, including complete, partial, not-started, edit, cancel, delete, completion-review, accessibility-label, and narrow-layout states.
- The real `fitness_ai.db` was not mutated.

See milestone memory: `docs/project_memory/milestones/workout_actuals_summary_v0.md`.

---

# Current State — Workout Completion Review UX v0.1

Current source of truth: `feature/workout-completion-review-ux-v0-1`.

Active workout milestone:

```text
Workout Completion Review UX v0.1
```

Requested status:

```text
WORKOUT_COMPLETION_REVIEW_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make workout completion intentional by showing a compact pre-completion review based on existing backend planned-vs-actual summary data.
```

Implemented scope:

- Changed the workout completion button so the first click opens an inline review instead of completing immediately.
- Added a compact completion review with logged/planned set count, exercise completion count, average RIR, and all-logged or missing-set status.
- Kept missing-set language neutral and allowed explicit completion anyway through the existing backend completion path.
- Added cancel behavior that returns to the normal active workout logging view.
- Kept the existing completed state, execution summary, saved sets, and previous-performance context visible after completion.
- Used the existing planned-vs-actual summary contract; no backend summary contract or completion semantics changed.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, recommendation behavior, nutrition, food logging, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Planned workout snapshots remain immutable.
- Actual set create/edit/delete behavior remains user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Completion remains explicitly user-triggered through the existing backend completion endpoint.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/workout_plans.py services/workout_plan_persistence_service.py tests/test_workout_plan_persistence_service.py`
- `npm run lint`
- `npm run build`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/workout_completion_review_ux_v0_1.md`.

---

# Current State — Workout Set Logging UX v0.1

Current source of truth: `feature/workout-set-logging-ux-v0-1`.

Active workout milestone:

```text
Workout Set Logging UX v0.1
```

Requested status:

```text
WORKOUT_SET_LOGGING_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make actual workout set logging faster and clearer while preserving the existing workout execution model and backend-owned logged-set truth.
```

Implemented scope:

- Added a backend actual-set delete path alongside the existing create/edit path.
- Added `DELETE /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}`.
- Kept actual-set delete scoped to the owning workout plan execution session and returned refreshed actual sets plus planned-vs-actual summary.
- Added frontend proxy support and typed client helpers for actual-set edit/delete.
- Updated workout exercise cards to show saved set rows, compact logged-set counts, and no-sets-yet states.
- Added inline saved-set edit controls for reps, weight, RIR, and notes.
- Added delete controls for mistaken actual sets.
- Preserved previous-performance context as read-only display.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, recommendation behavior, nutrition, food logging, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Planned workout snapshots remain immutable.
- Actual set values remain user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Existing workout preview/select/start/log/edit/complete/history and planned-vs-actual behavior remains stable.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_training_execution_summary_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/workout_plan_persistence_service.py api/routes/workout_plans.py tests/test_workout_plan_persistence_service.py`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint`
- `npm run build`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/workout_set_logging_ux_v0_1.md`.

---

# Current State — Workout Progression History v0

Current accepted source of truth: `main` after `ce5d316 Merge workout progression history v0`.

Accepted workout milestone:

```text
Workout Progression History v0
```

Accepted status:

```text
WORKOUT_PROGRESSION_HISTORY_V0_ACCEPTED_AND_MERGED
```

Purpose:

```text
Add compact previous-performance context to the workout flow so the user can see what they did last time for the same exercise.
```

Implemented scope:

- Added a read-only, user-scoped workout progression history service for completed planned workout executions.
- Added `POST /workout-plans/{user_id}/progression-history`.
- Summarized last completed session, recent best set, completed session count, logging quality, and no-history/limited-history states by exercise name.
- Kept public output bounded and excluded raw actual-set rows and notes.
- Added compact previous-performance display near workout preview/persisted exercise cards.
- Added a frontend proxy route, typed API helper, and TypeScript response models.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, workout mutation, recommendation behavior, nutrition, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Existing workout preview/select/start/log/edit/complete/history and planned-vs-actual behavior remains stable.
- Only completed planned workout executions are used for the public history surface.
- Incomplete set logging returns limited-state messaging rather than coaching claims.

See milestone memory: `docs/project_memory/milestones/workout_progression_history_v0.md`.

---

# Current State — Food Logging Edit UX v0.1

Current accepted source of truth: `main` after `a2bc7b3 Merge food logging edit UX v0.1`.

Accepted nutrition logging milestone:

```text
Food Logging Edit UX v0.1
```

Accepted status:

```text
FOOD_LOGGING_EDIT_UX_V0_1_ACCEPTED_AND_MERGED
```

Purpose:

```text
Make logged canonical food correction as usable as logging by supporting grams or backend-approved serving-unit edits while preserving canonical_food_id + resolved grams as persisted truth.
```

Implemented scope:

- Extended canonical log editing to accept either grams or `serving_unit_id` + `quantity`, never both.
- Serving-unit edits resolve to grams through backend serving-unit validation and recalculate macro snapshots.
- Serving-unit edits create or update serving metadata for the existing food entry.
- Grams edits clear stale serving metadata from previously serving-unit-backed entries.
- Meal-only edits preserve existing serving metadata.
- Delete removes associated serving metadata before deleting the food entry.
- Daily canonical logs now include optional public-safe serving context when present.
- Logged Today inline edit UI now supports grams fallback, approved serving-unit selection, previous serving-unit prefill, resolved grams preview, and macro preview.

Boundaries preserved:

- No favorites, meal templates, full diary/history, barcode scanning, AI food parsing, AI suggestions, meal planning, raw-source logging, target formula, Daily Coach, report, workout, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Backend remains responsible for serving-unit resolution, canonical nutrient snapshots, ownership checks, and persistence.
- Frontend remains a compact controller/renderer and does not invent nutrition values.
- Raw source payloads remain non-public.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_log_edit_serving_units_api.py tests/test_canonical_food_log_edit_serving_units_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_food_logging_recents_api.py tests/test_food_logging_recents_service.py tests/test_nutrition_target_vs_actual_service.py tests/test_api_smoke.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py services/nutrition_serving_unit_logging_service.py services/nutrition_serving_unit_service.py services/food_logging_recents_service.py tests`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint` and `npm run build` from `frontend`
- touched-file `git diff --check`

See milestone memory: `docs/project_memory/milestones/food_logging_edit_ux_v0_1.md`.

---

# Current State — Food Logging Recents v0

Current accepted source of truth: `main` after `merge-food-logging-recents-v0`.

Accepted nutrition logging milestone:

```text
Food Logging Recents v0
```

Accepted status:

```text
FOOD_LOGGING_RECENTS_V0_ACCEPTED_AND_MERGED
```

Purpose:

```text
Reduce daily food logging friction by deriving recent canonical foods from existing logs and letting the user quickly reselect the last-used grams or serving-unit context.
```

Implemented scope:

- Added a user-scoped recent canonical foods service derived from `food_entries`.
- Added `GET /nutrition/{user_id}/recent-canonical-foods?limit=10`.
- Returned distinct active canonical foods ordered by most recent log entry.
- Preserved grams-only context when serving metadata is absent.
- Preserved last serving-unit ID, serving label, quantity, and resolved grams when serving metadata is present.
- Kept recent result limits bounded and public-safe.
- Added a frontend recent-foods proxy and client helper.
- Updated the food logging card with compact Recent Foods chips that prefill grams or serving-unit context while preserving the canonical logging endpoint as the write path.

Boundaries preserved:

- No favorites, meal templates, full diary/history, barcode scanning, AI food parsing, meal planning, raw source logging, nutrition target, workout, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Backend remains responsible for serving-unit resolution and nutrition snapshots.
- Recent foods are derived from existing canonical logs; no new recents persistence was added.
- Raw source payloads remain non-public.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_target_vs_actual_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services api tests scripts`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint` and `npm run build` from `frontend`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/food_logging_recents_v0.md`.

---

# Current State — Serving Unit UX v0

Current source of truth: `feature/serving-unit-ux-v0`.

Active nutrition logging milestone:

```text
Serving Unit UX v0
```

Requested status:

```text
SERVING_UNIT_UX_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Allow canonical foods to be logged by grams or by backend-approved serving units while preserving canonical_food_id + resolved grams as the persisted source of truth.
```

Implemented scope:

- Extended canonical food logging so callers may submit either grams or `serving_unit_id` + `quantity`, but not both.
- Preserved existing grams logging behavior, canonical nutrient snapshots, daily actuals, and target-vs-actual rollups.
- Kept serving-unit logging backed by reviewed serving-unit rows and provenance metadata.
- Added public serving-unit discovery aliases for frontend use while keeping the earlier serving-unit response fields stable.
- Added starter serving-unit aliases for reviewed raw chicken breast and ground beef entries.
- Updated the food logging card to offer grams plus approved serving units, show resolved grams, and log the selected unit through the canonical endpoint.

Boundaries preserved:

- No real food promotion, barcode scanning, meal planning, AI/provider path, RAG, embeddings, vector search, agent orchestration, or nutrition semantic changes were added.
- Canonical foods still persist as canonical food ID plus resolved grams in `food_entries`; serving-unit metadata remains supporting provenance.
- No DB snapshots, ZIPs, raw source payloads, or runtime reports are part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_nutrition_serving_unit_data_model_v1.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_target_vs_actual_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_api_smoke.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services api tests scripts`
- `.\.venv\Scripts\python.exe -m ruff format --check` on touched Python files
- `npm run lint` and `npm run build` from `frontend`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/serving_unit_ux_v0.md`.

---

# Current State — Exercise Rotation Coverage v0

Current source of truth: `feature/exercise-rotation-coverage-v0`.

Active backend workout milestone:

```text
Exercise Rotation Coverage v0
```

Requested status:

```text
EXERCISE_ROTATION_COVERAGE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Increase deterministic workout exercise coverage so preview rotation can use most equipment-compatible, generator-eligible curated catalog exercises over time while preserving safety constraints, movement balance, workout sizing, and selected-workout immutability.
```

Implemented scope:

- Added a catalog-driven workout rotation pool service that appends safe catalog candidates after existing deterministic anchor options.
- Expanded lower, push, pull, accessory, core, carry, arms, upper-back, and conditioning-compatible deterministic slots without rewriting workout templates.
- Preserved existing anchors, preview variation behavior, recent-exercise penalties, equipment filtering, unavailable-equipment filtering, duplicate-name protection, and same-workout rotation-group protection.
- Enforced avoid movements and movement restrictions against hard-coded anchors as well as catalog-expanded options.
- Kept mobility entries out of generator pools and kept internal/external rotation drills out of primary pull slots.
- Extended the exercise catalog utilization diagnostic with generator-eligible counts, full candidate names, selected exercise types, not-selected reasons, and slot-family candidate pool sizes.
- Added Exercise Rotation Coverage v0 tests and updated older utilization/eligibility expectations for the broader catalog reachability.

Diagnostic result:

```text
Pre-change local 25-variation sweep: 69 unique selected exercises.
Final local 25-variation sweep: 126 unique selected exercises.
Total active catalog exercises: 240.
Equipment-eligible home-gym exercises: 237.
Generator-eligible home-gym exercises: 224.
Equipment-eligible not in candidate options: 18.
Generator-eligible not selected in sweep: 98.
Selected movement patterns: 13.
```

The v0 target of roughly 120+ unique selected exercises was achieved without selecting mobility as an exercise type.

Boundaries preserved:

- No provider, OpenAI, Ollama, CrewAI, RAG, embeddings, vector search, agent orchestration, frontend, database schema, food catalog, nutrition/serving, clinical/rehab, periodization, progression, or 1RM changes were added.
- No exercise catalog entries were added.
- No DB, generated JSON report, snapshot, ZIP, or temporary runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_exercise_rotation_coverage_v0.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_exercise_catalog_service.py tests/test_exercise_eligibility_matrix_v1.py tests/test_exercise_catalog_utilization_specialized_movement_coverage_v1.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services tools tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services tools tests`
- `git diff --check`

---

# Current State — Canonical Food Bulk Catalog Builder Hardening v0.1

Current source of truth: `feature/canonical-food-bulk-catalog-builder-hardening-v0-1`.

Active backend hardening milestone:

```text
Canonical Food Bulk Catalog Builder Hardening v0.1
```

Requested status:

```text
CANONICAL_FOOD_BULK_CATALOG_BUILDER_HARDENING_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Harden bulk canonical food catalog curation before any real promotion by preserving meaningful food qualifiers and reducing false skipped_duplicate_name results.
```

Implemented scope:

- Preserved meaningful qualifiers for common bulk catalog families before duplicate-name checks.
- Added specific display names for flour, cheese, rice, oats, tomato, butter, cream, bread, and oil variants.
- Fixed over-broad oil curation so `Anchovies, canned in olive oil` becomes `Canned anchovies`, not `Olive oil`.
- Kept raw meat/fowl/fish protection intact while preserving clearly prepared/canned/ready-to-eat eligibility.
- Kept true duplicate protection for same normalized display name plus same macro profile.
- Added fallback naming for materially different same-name rows so the builder can use a more specific second-phrase display name instead of immediately skipping.
- Extended bulk catalog tests for qualifier preservation, true duplicate skips, anchovy/oil curation, representative dry-run improvement, and idempotency regression coverage.

Boundaries preserved:

- No real promotion run is authorized or performed.
- No frontend files, food logging UI, serving picker, diary/history, admin UI, raw USDA review UI, AI parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_bulk_catalog_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `git diff --check`

---

# Current State — Canonical Food Bulk Catalog Builder v0

Current source of truth: `feature/canonical-food-bulk-catalog-builder-v0`.

Active backend implementation milestone:

```text
Canonical Food Bulk Catalog Builder v0
```

Requested status:

```text
CANONICAL_FOOD_BULK_CATALOG_BUILDER_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Promote many safe, practical USDA Foundation raw source rows into searchable/loggable canonical foods through deterministic inventory, category safety, dry-run, report, and idempotent promotion tooling.
```

Implemented scope:

- Added `scripts/inspect_usda_food_catalog_sources.py` for read-only source inventory reports across raw source rows, macro coverage, canonical counts, and optional FDC CSV data type/category counts.
- Enriched FDC directory import with optional `food_category.csv` lookup so imported `foundation_food` rows can store readable category names.
- Added `services/food_bulk_catalog_service.py` for category-gated bulk candidate selection and promotion through the existing raw-source promotion service.
- Added `scripts/promote_canonical_food_bulk_catalog.py` with `--db-path`, `--dry-run`, `--source-name`, `--include-data-types`, `--include-categories`, `--exclude-categories`, `--limit`, `--max-promotions`, and `--report-path`.
- Added report buckets for `promoted`, `already_promoted`, `skipped_missing_macros`, `skipped_unsafe_raw`, `skipped_category`, `skipped_duplicate_name`, `skipped_ambiguous`, and `skipped_invalid`.
- Added duplicate-name protection so broad catalog runs do not overwrite existing/manual canonical nutrients when multiple source rows curate to the same display name.
- Preserved raw produce eligibility and skipped raw/not-clearly-prepared meat, fowl, and fish rows.

Boundaries preserved:

- No frontend changes, food logging UI changes, serving picker, food diary/history, admin curation UI, raw USDA review UI, AI food parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration was added.
- USDA imports still default to `foundation_food`; no FNDDS, SR Legacy, branded, sample, sub-sample, market acquisition, or agricultural acquisition expansion was added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_bulk_catalog_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services scripts tests`
- `git diff --check`

---

# Current State — Canonical Food Starter Set Promotion Pack v0

Current source of truth: `feature/canonical-food-starter-set-promotion-pack-v0`.

Active backend implementation milestone:

```text
Canonical Food Starter Set Promotion Pack v0
```

Requested status:

```text
CANONICAL_FOOD_STARTER_SET_PROMOTION_PACK_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expand practical everyday canonical food availability by promoting high-confidence starter foods from existing raw source records without importing datasets or fabricating nutrition values.
```

Implemented scope:

- Added a reviewable 67-item starter-set definition across proteins, carbs/starches, fruits, vegetables, dairy/fats, and common extras.
- Added deterministic matching against existing `raw_food_source_records`, defaulting to USDA `foundation_food` rows with macro data.
- Added conservative report buckets: `matched`, `skipped_missing`, `skipped_ambiguous`, `skipped_raw_only`, and `already_promoted`.
- Added `scripts/promote_canonical_food_starter_set.py` with required `--db-path`, `--dry-run`, optional `--limit`, `--include-categories`, and `--report-path`.
- Reused the existing raw-source promotion service for canonical food creation/reuse, aliases, macro nutrient sync, and source provenance.
- Preserved idempotency by reporting existing primary source links as `already_promoted`.
- Preserved raw produce eligibility while skipping raw/uncooked meat, fowl, and fish as everyday starter entries.

Boundaries preserved:

- No full USDA import expansion, new dataset type, admin UI, manual review UI, serving picker, food diary/history, edit/delete change, food logging UI change, workout change, recovery change, AI food parsing, barcode scanning, image recognition, RAG, embeddings, vector search, or agent orchestration was added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services scripts tests`
- `git diff --check`

---

# Current State — Edit/Delete Logged Food v0

Current accepted baseline:

```text
53c559a Merge food log grouping and workout prose cleanup v0
```

Active full-stack implementation milestone:

```text
Edit/Delete Logged Food v0
```

Requested status:

```text
EDIT_DELETE_LOGGED_FOOD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add safe edit/delete support for today's logged canonical foods while preserving backend-owned nutrition truth and compact Today UI scope.
```

Implemented scope:

- Added `PATCH /nutrition/{user_id}/canonical-logs/{entry_id}` for editing grams and meal type.
- Added `DELETE /nutrition/{user_id}/canonical-logs/{entry_id}` for deleting one canonical logged-food entry.
- Added backend service helpers that require `entry_id` and `user_id`, with optional selected-date guards.
- Recalculated stored macro snapshots when grams change so canonical logs and canonical totals reflect edits.
- Preserved missing macro values as `null` and explicit zero macro values as `0`.
- Preserved canonical food identity; edit does not change canonical food, food name, or entry date.
- Delete removes only the owned `food_entries` row and does not delete canonical foods, nutrients, aliases, or source links.
- Added frontend proxy/helper support for PATCH and DELETE.
- Added compact inline `Edit`, `Save`, `Cancel`, and two-step `Delete` controls to the grouped `Logged today` list.
- Refreshed the logged-food list and server-rendered Today nutrition after edit/delete through the existing local event plus `router.refresh()`.

Ownership and validation behavior:

- Wrong-user edits/deletes return a clean not-found response.
- Missing entry IDs return a clean not-found response.
- Selected-date mismatch returns a clean not-found response when the frontend sends the date guard.
- Invalid grams are rejected.
- Meal type is normalized/validated to `breakfast`, `lunch`, `dinner`, `snack`, or `other`.

Boundaries preserved:

- No full food diary/history, multi-date editor, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, raw USDA source review UI, canonical promotion UI, workout changes, recovery changes, or broad Today redesign was added.
- Raw USDA/source rows are not logged or mutated directly.
- Backend nutrition actuals remain backend-owned through existing `food_entries` and nutrient rollup paths.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State — Today Food Log Grouping + Workout Prose Cleanup v0

Current accepted baseline:

```text
ced70d0 Merge Today logged foods read-only list v0
```

Active frontend implementation milestone:

```text
Today Food Log Grouping + Workout Prose Cleanup v0
```

Requested status:

```text
TODAY_FOOD_LOG_GROUPING_WORKOUT_PROSE_CLEANUP_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make the Today logged-food and Workout detail surfaces more compact, grouped, and data-first without changing backend contracts.
```

Implemented scope:

- Grouped the read-only `Logged today` food list by normalized meal type.
- Rendered known meal types as Breakfast, Lunch, Dinner, and Snack; missing or unknown values render as Other.
- Hid empty meal groups while preserving the compact empty-day state.
- Kept explicit zero macro values visible and omitted missing macro values from compact rows.
- Added compact per-meal item counts and a bounded logged-food scroll area for longer days.
- Put `Logged today` and `Today's Workout` side-by-side in the Today primary column on wide desktop viewports.
- Preserved mobile order as Nutrition, Log Food, Logged today, Today's Workout, Recovery.
- Removed low-value deterministic prose from the Workout page hero and Session Status area.
- Removed the Workout page Session Notes card rather than relocating generic deterministic prose.
- Changed Workout detail exercise cards to a two-column desktop grid and single-column mobile layout.
- Preserved existing active workout logging controls.

Boundaries preserved:

- Backend behavior and contracts were not changed.
- Food search, food logging, logged-food refresh, Nutrition actual refresh, Today workout detail navigation, active workout logging, and Recovery Check-In behavior were not intentionally changed.
- No edit/delete food logs, full food diary/history, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, provider behavior, recovery logic changes, nutrition calculation changes, food search changes, or AI workout prose generation were added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State — Today Logged Foods Read-Only List v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active full-stack implementation milestone:

```text
Today Logged Foods Read-Only List v0
```

Requested status:

```text
TODAY_LOGGED_FOODS_READONLY_LIST_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make today's food logging loop visible by showing a compact read-only list of canonical foods logged for the selected user/date near Nutrition and Log Food.
```

Implemented scope:

- Added a read-only backend endpoint at `GET /nutrition/{user_id}/canonical-logs?date=YYYY-MM-DD`.
- Added a nutrition service helper that reads only canonical food entries for the selected user/date.
- Returned stored macro snapshots from `food_entries` so missing macros remain `null` and explicit zero values remain `0`.
- Preserved canonical food IDs and friendly food names without exposing raw USDA payloads or raw source identifiers.
- Added a compact `Logged today` component under Log Food on the Today page.
- Kept the left-column order as Nutrition, Log Food, Logged today, Today's Workout.
- Preserved `router.refresh()` after food logging so Nutrition actuals and the logged-food list reload together.
- Added a clean empty state: `No foods logged yet today.`

Boundaries preserved:

- No edit/delete food log flow was added.
- No food history across dates, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image food recognition, raw USDA review UI, or canonical promotion UI was added.
- Nutrition calculations, canonical logging behavior, workout, recovery, provider behavior, and user routing were not changed.
- Full USDA datasets, generated DB files, ZIPs, CSVs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State — Canonical Food Search Result Curation v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Search Result Curation v0
```

Requested status:

```text
CANONICAL_FOOD_SEARCH_RESULT_CURATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Improve canonical food search result quality so daily food logging returns practical, human-friendly canonical food results instead of raw USDA-style names.
```

Implemented scope:

- Added a deterministic canonical display-name curation helper for public search labels and raw-source promotion.
- Kept canonical search on `canonical_food_id`; raw USDA source rows still do not become direct log targets.
- Preserved source identity through existing source links and compact `source` summaries.
- Added conservative practical labels such as `Chicken breast`, `Hummus`, `2% milk`, `Egg`, `Oatmeal`, and `Grape tomatoes`.
- Preserved raw meat/fowl/fish truth by keeping explicit raw names visibly raw, such as `Chicken breast, raw`.
- Added a default search-ranking penalty for raw meat/fowl/fish canonical foods unless the user explicitly searches `raw` or `uncooked`.
- Kept non-meat raw foods, such as raw tomatoes, eligible for normal search results.
- Added starter curation aliases during seed so practical names can be found without changing nutrient values.
- Adjusted oatmeal seeding so `oatmeal` prefers cooked oatmeal while `oats` still finds dry oats.

Boundaries preserved:

- No frontend files were changed.
- No canonical logging behavior, nutrition rollup behavior, serving-unit behavior, workout, recovery, provider, or user-routing behavior changed.
- No full USDA taxonomy, admin curation UI, raw source review UI, food diary/history, edit/delete logs, serving picker, meal builder, barcode scanner, AI food parser, or image recognition was added.
- Nutrient values, missing macro behavior, explicit zero macro behavior, and source payload privacy remain unchanged.
- Full USDA datasets, generated SQLite DBs, ZIPs, CSVs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py`

---

# Current State — Today Workout Detail UX Refinement v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Today Workout Detail UX Refinement v0
```

Requested status:

```text
TODAY_WORKOUT_DETAIL_UX_REFINEMENT_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Refine the Today and Workout detail screens after the main-loop density polish so the daily workout loop is more compact, data-rich, and less repetitive.
```

Implemented scope:

- Reworked the Today page into independent desktop column stacks so Today's Workout sits directly below Log Food instead of being pushed down by the taller Recovery Check-In card.
- Preserved mobile Today order as Nutrition, Log Food, Today's Workout, Recovery Check-In.
- Reused existing current-workout payload data to show compact Today exercise rows with set completion, reps, weight, and RIR when actual set data is available.
- Kept planned-only Today workout rows compact with planned set and rep detail.
- Tightened the Workout detail hero/status card into a compact Session Status card.
- Removed redundant completed-workout status copy from the Workout detail hero/status area.
- Moved Execution Summary above Session Notes and gave it a more prominent visual treatment.
- Kept Session Notes available below Execution Summary.

Boundaries preserved:

- Backend behavior and contracts were not changed.
- Nutrition logging, canonical food search/logging, recovery scoring, workout lifecycle, workout logging/completion, provider behavior, and user routing were not changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, USDA curation UI, dashboard layout framework, or collapsible-card system was added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State — Today Main Loop Density Polish v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Today Main Loop Density Polish v0
```

Requested status:

```text
TODAY_MAIN_LOOP_DENSITY_POLISH_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Polish the Next.js Today page into a compact operator dashboard for the real daily loops: Nutrition / Log Food, Workout summary, and Recovery Check-In.
```

Implemented scope:

- Removed the giant green Next Action card from prime Today page real estate.
- Moved Nutrition and Log Food to the top of the Today layout.
- Kept Nutrition and Log Food as adjacent existing components instead of adding a new combined nutrition system.
- Compacted the Food Logging selected state so selected food appears once, search results hide after selection until the query changes, macro preview is inline, and success/error messages are small.
- Converted completed workout state into a compact summary using existing Today workout payload data.
- Removed redundant completed-workout instructional copy from the Today summary surface.
- Preserved Recovery Check-In behavior while removing the internal-ish Recovery eyebrow.
- Preserved mobile order as Nutrition / Log Food, Workout, then Recovery.

Boundaries preserved:

- No backend behavior, nutrition aggregation, canonical logging, recovery scoring, workout lifecycle, provider, or user-routing behavior changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, dashboard state manager, or collapsible-card framework was added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State — Next.js Canonical Food Logging UI v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Canonical Food Logging UI v0
```

Requested status:

```text
NEXTJS_CANONICAL_FOOD_LOGGING_UI_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the first small Next.js food logging surface so users can search canonical foods, enter grams, log food, and see Today nutrition actuals refresh through the existing backend contract.
```

Implemented scope:

- Added a compact `FoodLoggingCard` near the existing Today Nutrition card.
- Added Next.js proxy routes for canonical food search and canonical food logging.
- Reused the existing backend canonical search route and canonical logging route without exposing raw USDA rows.
- Added client-side macro preview from per-100g canonical nutrient data.
- Refreshed Today after save with `router.refresh()` so Nutrition actuals update through the existing Today contract.
- Preserved current `user_id` and date selection when searching and logging food.
- Added a backend runtime SQLite schema-init hotfix so older local `food_entries` tables receive canonical logging columns on FastAPI startup without deleting existing DB data.

Boundaries preserved:

- No serving picker, meal builder, barcode flow, AI food parser, favorites, recent foods, food diary history, or raw USDA review UI was added.
- No backend nutrition aggregation path was changed.
- No workout, recovery, provider, or user-switcher behavior was changed.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State — Today Nutrition Logged Totals Integration v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Today Nutrition Logged Totals Integration v0
```

Requested status:

```text
TODAY_NUTRITION_LOGGED_TOTALS_INTEGRATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Connect canonical food logging to the existing Today nutrition card by proving the Today backend contract reflects canonical food log actuals through the shared target-vs-actual path.
```

Implemented scope:

- Confirmed the existing Today backend already sources nutrition actuals from `build_target_vs_actual_nutrition_summary(...)`.
- Confirmed canonical food logs already flow into that path through `food_entries`, so no second Today-specific canonical rollup was added.
- Added Today service and Today route integration tests that log canonical foods and verify the Today nutrition payload updates by the expected macro delta exactly once.
- Added focused Today tests for user/date separation and clean no-log-day behavior.
- Preserved the existing compact frontend Nutrition Macro Card without redesign or code changes.

Boundaries preserved:

- No food search UI, food logging UI, serving picker, meal builder, barcode flow, or AI food parser was added.
- No raw USDA source identifier became a Today input.
- No workout, recovery, provider, USDA import, or canonical-promotion behavior was changed.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py tests/test_daily_driver_contract_models.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/daily_driver_today_service.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/daily_driver_today_service.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py`

---

# Current State — Next.js Today Workout UI Polish v0

---

# Current State — Canonical Food Logging Backend v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Logging Backend v0
```

Requested status:

```text
CANONICAL_FOOD_LOGGING_BACKEND_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the backend write path that logs canonical foods by canonical_food_id and grams so daily nutrition tracking can consume the curated canonical food pipeline without exposing raw USDA rows directly.
```

Implemented scope:

- Hardened the existing canonical logging route at `POST /nutrition/{user_id}/log-canonical`.
- Preserved the canonical-only logging rule with `canonical_food_id` as the user-facing identifier.
- Persisted canonical linkage and canonical macro snapshots on `food_entries`.
- Preserved grams as the logging calculation source of truth.
- Added a canonical-only daily macro rollup helper plus a small read route for daily rollup totals.
- Kept the existing legacy nutrition actuals path working through the current write-through mirror behavior.
- Added focused tests for persisted canonical linkage, invalid input, missing-vs-zero macro behavior, user/date separation, and rollup output.

Boundaries preserved:

- No Next.js UI, food search UI, meal builder, serving-size UX, barcode flow, or AI food parser was added.
- No raw USDA identifier became the normal logging path.
- No workout, recovery, provider, or user-switcher behavior was touched.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py tests/test_food_normalization_service.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check database.py services/nutrition_service.py api/routes/nutrition.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check database.py services/nutrition_service.py api/routes/nutrition.py tests/test_canonical_food_logging_api.py`

---

# Current State — Canonical Food Search API v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Search API v0
```

Requested status:

```text
CANONICAL_FOOD_SEARCH_API_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add a tightly scoped backend search API for canonical foods only so future food logging/search stays on curated canonical foods and not raw USDA source rows.
```

Implemented scope:

- Hardened the canonical food search route at `GET /foods/canonical/search`.
- Preserved canonical-only search behavior through `canonical_foods` and alias search.
- Added compact default source summary output when a canonical food has a linked source row.
- Preserved macro summaries from canonical nutrient rows only.
- Made empty search queries return a safe empty result.
- Kept deterministic matching order and tightened alias ordering.
- Added focused tests for promoted canonical foods, compact source identity, and missing-vs-zero macro behavior.

Boundaries preserved:

- No food logging backend or UI was added.
- No raw USDA direct-search endpoint was added.
- No meal builder, barcode, AI food parsing, workout, recovery, or provider behavior was touched.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_promotion_service.py tests/test_food_normalization_service.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py`

---

# Current State — USDA Raw Source Canonical Promotion v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Raw Source Canonical Promotion v0
```

Requested status:

```text
USDA_RAW_SOURCE_CANONICAL_PROMOTION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create a narrow backend bridge from USDA raw source rows into the existing curated canonical food tables so future food search/logging stays canonical and not raw-source-backed.
```

Implemented scope:

- Added a focused backend review helper for listing promotable USDA raw source rows.
- Defaulted promotion-review queries to `foundation_food`, with override support for review-mode inclusion of non-default USDA hierarchy rows.
- Added a deterministic promotion path from `raw_food_source_records` into `canonical_foods`, `canonical_food_aliases`, `canonical_food_nutrients`, and `food_source_links`.
- Preserved USDA source identity through `source_name`, `source_record_id`, and the linked internal raw source record id.
- Reused existing canonical-food tables and upsert behavior instead of adding a parallel canonical subsystem.
- Preserved missing macro values as absent and explicit `0` values as `0` during canonical nutrient sync.
- Added an opt-in scratch-database CLI for promotion smoke and focused service tests for idempotency, source-link preservation, review filtering, and macro handling.

Boundaries preserved:

- No food search UI, food logging UI, barcode flow, meal builder, or AI food parsing was added.
- Raw USDA rows still do not become the direct user-facing search path.
- Full USDA datasets and generated DB files remain local-only artifacts.
- Frontend, workout, recovery, and provider behavior were not touched.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/food_normalization_models.py services/food_canonical_promotion_service.py scripts/promote_usda_raw_food.py tests/test_food_canonical_promotion_service.py`
- `.\.venv\Scripts\python.exe -m ruff format --check models/food_normalization_models.py services/food_canonical_promotion_service.py scripts/promote_usda_raw_food.py tests/test_food_canonical_promotion_service.py`

---

# Current State — USDA Import Loggable Foundation Filter v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Import Loggable Foundation Filter v0
```

Requested status:

```text
USDA_IMPORT_LOGGABLE_FOUNDATION_FILTER_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Hotfix the USDA real-dataset directory importer so extracted FoodData Central CSV imports default to loggable top-level foundation_food rows instead of mostly sample/subsample/acquisition hierarchy rows.
```

Implemented scope:

- Preserved the existing simple `--input` USDA-style CSV import path.
- Preserved extracted FoodData Central `--fdc-dir` import support.
- Defaulted real FDC directory imports to `foundation_food`.
- Added `--include-data-types` override support for review-mode imports.
- Moved `--limit` application to after FDC `data_type` filtering.
- Preserved `source_record_id` as the USDA FDC ID and kept `fdc_id` in `source_payload_json`.
- Preserved missing joined macro nutrients as `NULL` / `None` while keeping explicit USDA zero values as `0`.
- Skipped negative joined macro values so malformed USDA macro rows do not abort the import or store negative macros.
- Added focused real-shape fixture coverage for default filtering, override behavior, post-filter limits, and null-vs-zero macro handling.

Boundaries preserved:

- No food search UI, food logging UI, or canonical-food promotion flow was added.
- Full USDA datasets and generated DB files remain local-only artifacts.
- Backend remains the owner of imported source metadata and macro truth.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Today Workout UI Polish v0
```

Requested status:

```text
NEXTJS_TODAY_WORKOUT_UI_POLISH_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Polish the existing Next.js Today and Workout screens so they feel tighter and more useful for daily use without changing backend workout, recovery, nutrition, or user-routing behavior.
```

Implemented scope:

- Tightened the Today header into a shorter card with long readable date formatting and inline user selection.
- Removed normal UI clutter that labeled users as `Real user`, `QA / Test User`, or `(Test)`.
- Reworked the Today workout summary card to use plain app language, remove generated workout titles from the summary surface, and promote the workout-detail action.
- Tightened the Workout page header and removed backend-ish preview wording.
- Simplified the Workout experience layout by removing `Preview Details`, shrinking the summary area, and moving preview actions to the top of the exercises card.
- Kept session notes smaller and conditional so low-value note content no longer creates a large side panel.

Boundaries preserved:

- No backend behavior or workout contracts were changed.
- URL `user_id` remains the source of truth.
- Workout preview/select/start/logging/completion flows remain on their existing API and component path.
- Recovery Check-In and Nutrition Macro Card behavior remain unchanged.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State — USDA Real Dataset Adapter Smoke v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Real Dataset Adapter Smoke v0
```

Requested status:

```text
USDA_REAL_DATASET_ADAPTER_SMOKE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Extend the local USDA import foundation so the repo can ingest the real extracted FoodData Central CSV directory shape while keeping nutrition scope small and preserving the current raw-source boundaries.
```

Implemented scope:

- Reused the existing USDA raw-source importer foundation and shared upsert path into `raw_food_source_records`.
- Added a real FoodData Central directory importer that joins `food.csv`, `food_nutrient.csv`, and `nutrient.csv`, with optional `branded_food.csv` metadata.
- Preserved the original simple fixture CSV import path so current tiny-fixture workflows still work.
- Added defensive macro mapping from USDA nutrient definitions for calories, protein, carbs, and fat.
- Added CLI support for `--fdc-dir` and optional `--limit` for smoke-sized local imports.
- Added a tiny checked-in extracted-directory fixture plus focused tests covering joins, optional metadata omission, rerun idempotence, row limiting, and CLI directory import.

Boundaries preserved:

- No fake food database, meal database, AI food parser, or long-term nutrition logging system was added.
- Canonical foods and user-facing food search/logging remain unchanged.
- Full USDA data extracts remain local-only and ignored by Git.
- Backend remains the owner of imported source metadata and normalized macro truth.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/usda_food_data_models.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
- `.\.venv\Scripts\python.exe -m ruff format --check models/usda_food_data_models.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

---

# Current State — USDA Food Data Import Foundation v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Food Data Import Foundation v0
```

Requested status:

```text
USDA_FOOD_DATA_IMPORT_FOUNDATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create a repeatable local USDA FoodData Central import foundation that stores USDA-backed raw food source rows locally without committing full datasets or changing user-facing food logging behavior yet.
```

Implemented scope:

- Reused the existing two-layer nutrition catalog architecture built around `raw_food_source_records` and canonical foods.
- Extended `raw_food_source_records` to preserve USDA-ready metadata including `data_type`, `gtin_upc`, serving metadata, normalized per-100g macros, and `import_batch`.
- Added a deterministic USDA CSV importer service that validates required columns, preserves `fdc_id`, upserts by `source_name + source_record_id`, and stores source payload metadata locally.
- Added a CLI importer at `scripts/import_usda_food_data.py` with optional scratch DB override support.
- Added a tiny checked-in USDA-style fixture for tests only.
- Added focused tests covering schema expansion, fixture import, optional-field handling, idempotent re-import behavior, invalid input handling, and CLI help.
- Added ignored local USDA data paths so full source downloads stay out of Git.

Discovered existing nutrition persistence:

- Legacy nutrition actuals still read through `foods`, `food_nutrients`, and `food_entries`.
- App-facing search/logging uses curated canonical food tables plus source-link metadata.
- A staged catalog importer already existed under `tools/`, but it writes review artifacts only and does not populate the local database.
- This milestone adds the first repeatable local database import path for USDA-backed source rows.

Boundaries preserved:

- Canonical app-facing foods remain curated and unchanged by this importer.
- No food logging UI, food search UI, meal builder, barcode flow, AI food parsing, or provider behavior was added.
- No full USDA dataset, archive, or generated SQLite database was committed.
- Backend remains the owner of source metadata, macro normalization, and future catalog promotion boundaries.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_routes.py tests/test_daily_driver_today_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/food_normalization_models.py models/usda_food_data_models.py services/food_normalization_service.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

---

# Current State — Next.js Nutrition Macro Card v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Nutrition Macro Card v0
```

Requested status:

```text
NEXTJS_NUTRITION_MACRO_CARD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expose a small nutrition status surface on the Next.js Today page by reusing existing backend-owned nutrition targets and logged macro actuals without introducing a new food logging system.
```

Implemented scope:

- Reused the existing backend-owned Today contract and nutrition target-vs-actual service as the source of nutrition truth.
- Extended the Today nutrition summary to expose carbohydrate and fat targets plus logged carbohydrate and fat actuals alongside calories and protein.
- Added a compact Next.js Nutrition Macro Card for Today that shows calories, protein, carbs, and fat with a simple status line.
- Added a clean empty-state message when no nutrition has been logged yet for the selected user/date.
- Preserved `user_id` routing through the existing Today query flow.
- Added focused contract, route, and service test coverage for the expanded nutrition summary.

Explicit deferral:

- Manual macro total entry/update was deferred in this milestone.
- The repo has nutrition logging routes for canonical foods/servings, but it does not have a small existing backend path for direct daily macro-total persistence.
- No fake food database, meal database, AI food parser, or parallel nutrition write model was added.

Boundaries preserved:

- Backend remains the owner of nutrition targets, logging actuals, comparisons, and safe wording boundaries.
- No nutrition target logic was moved into the frontend.
- No Streamlit nutrition changes were added.
- No USDA import, searchable foods table, meal builder, barcode flow, or long-term nutrition logging architecture was added.
- No provider, RAG, vector, or agent behavior was added.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_routes.py tests/test_daily_driver_today_service.py -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

---

# Current State — Workout Generation + Today Workout View v0

Current accepted baseline:

```text
9192863 Merge nextjs mobile today shell v0
```

Active frontend implementation milestone:

```text
Workout Generation + Today Workout View v0
```

Requested status:

```text
WORKOUT_GENERATION_TODAY_VIEW_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expose the existing backend-owned workout generation and planned-workout flow through the Next.js daily-driver frontend so normal daily workout viewing no longer depends on Streamlit.
```

Implemented scope:

- Inspected and reused the existing workout planning path built around `services/workout_daily_state_service.py`, `services/workout_plan_persistence_service.py`, `services/workout_plan_service.py`, `api/routes/workout_plans.py`, and the existing Streamlit Workout/Today wiring.
- Added a typed backend workout detail contract at `GET /api/today/workout`.
- Added `models/today_workout_view_models.py` and `services/today_workout_view_service.py`.
- Reused current-day persisted workout execution state when it exists.
- Reused existing deterministic workout generation as a read-only preview when no current-day persisted plan exists.
- Added focused backend tests for the new workout contract, service, and route.
- Added frontend types and API client support for the workout detail contract.
- Added a new Next.js route at `frontend/src/app/today/workout/page.tsx`.
- Wired the Today Workout card to the workout detail page.
- Wired the Next Action card to the workout detail page when the next action is workout-related.
- Preserved mobile stacked rendering while adding a practical desktop workout detail layout.

Files changed:

- `api/routes/daily_driver.py`
- `models/today_workout_view_models.py`
- `services/today_workout_view_service.py`
- `tests/test_today_workout_view_models.py`
- `tests/test_today_workout_view_service.py`
- `tests/test_today_workout_route.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/today/workout/page.tsx`
- `frontend/src/components/NextActionCard.tsx`
- `frontend/src/lib/dailyDriverApi.ts`
- `frontend/src/lib/todayWorkoutApi.ts`
- `frontend/src/types/todayWorkout.ts`

Boundaries preserved:

- Backend remains the owner of readiness, workout, nutrition, and next-action truth.
- No backend truth was invented in the frontend.
- No auth, hosting, sync, or multi-user work was added.
- No PostgreSQL work was added.
- No workout logging or nutrition logging was added.
- No provider execution, OpenAI, Ollama, or CrewAI work was added.
- No raw provider internals are exposed in the UI.
- No Markdown rendering or rich-text rendering was added for coach note.
- No Streamlit redesign or Streamlit removal was added.
- No backend Python write-path behavior was added for workout logging or selection.
- No parallel frontend workout engine was created.

Validation recorded:

- `git diff --check`
- targeted `ruff check` on touched Python files
- targeted `black --check` on touched Python files
- `py_compile` on touched Python files
- `python -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py tests/test_today_workout_view_models.py tests/test_today_workout_view_service.py tests/test_today_workout_route.py tests/test_workout_daily_state_lifecycle_v1.py -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

Open limitations:

- This milestone exposes workout viewing only. It does not add full workout logging controls to Next.js.
- The preview path is read-only and uses existing deterministic workout generation without mutating workout lifecycle state.
- Linux runtime-box manual smoke is still required for final runtime confirmation outside this Windows implementation pass.

Reference-only continuity anchors remain preserved:

```text
Project Memory Alignment + North Star Architecture v1
feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
reference-only
No provider may run on normal Today page load
Provider Narrative QA Matrix v2
Daily Coach Same-Session Approved Preview Bridge v1 Retry
Same-Session Bridge Runtime QA v1
Daily Coach Narrative Product Voice Polish v1
Daily Coach Narrative Product Voice Runtime QA v1
PASS_WITH_NOTE
sound right and be right
Local Developer Command Menu Audit + Repo-Owned Commands v1
scripts/fitness_commands.ps1
Local Command Menu App Runtime Correction v1
Linux is the canonical
wapp
Daily Coach Async Service Shell / No Worker v1
service shell only
no provider execution added
```

---

# Current State — Daily Driver Core Contract v0

Current accepted baseline:

```text
df2a56f Merge daily coach gpt family human voice trial v1
```

Active backend implementation milestone:

```text
Daily Driver Core Contract v0
```

Requested status:

```text
DAILY_DRIVER_CORE_CONTRACT_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create the first backend-owned daily-driver Today contract so the app can answer what to do today without requiring provider calls or a frontend rebuild.
```

Implemented scope:

- Added typed Daily Driver contract models for readiness, workout, nutrition, next action, coach note, and the Today response.
- Added a deterministic `build_daily_driver_today_response()` service that composes existing backend-owned recovery, workout, nutrition, and next-action facts.
- Added a minimal `GET /api/today` route with `user_id` and `date` inputs.
- Added focused model, service, and route tests for the new contract.
- Kept `coach_note` optional and disabled by default for v0.
- Preserved graceful fallback behavior through `data_gaps` and `limitations` when some daily data is sparse.

Boundaries preserved:

- SQLite remains the current data store.
- No PostgreSQL work was added.
- No auth, hosting, sync, or multi-user work was added.
- No Next.js or frontend-shell work was added.
- No Streamlit redesign was added.
- No provider expansion or provider promotion was added.
- No OpenAI, Ollama, or CrewAI call is required for the Today contract.
- No raw provider internals are exposed in user-facing Today fields.
- No Markdown is allowed in product-facing coach note text.
- Backend remains the owner of readiness, workout, nutrition, and next-action truth.

---

# Current State — Daily Coach GPT Family Human Voice Trial v1

Current accepted baseline:

```text
05313fd Merge daily coach human voice prompt contract v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_05313fd_main_merge-daily-coach-human-voice-prompt-contract-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Human Voice Prompt Contract v1
```

Active backend implementation milestone:

```text
Daily Coach GPT Family Human Voice Trial v1
```

Requested status:

```text
DAILY_COACH_GPT_FAMILY_HUMAN_VOICE_TRIAL_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Use the accepted human-editable Daily Coach prompt preview lane to compare GPT-family model output against the same raw backend provider-preview payload.
```

Implemented scope:

- Added a developer-only OpenAI/GPT-family provider path for the human voice prompt preview lane.
- Added a multi-model comparison tool at `tools/dev_daily_coach_gpt_family_human_voice_trial.py`.
- Extended `tools/dev_daily_coach_human_voice_prompt_preview.py` with explicit `--provider openai` support.
- Preserved `--provider ollama` and `--mock-output` developer smoke behavior.
- Model IDs are CLI-configurable and not hardcoded as final truth.
- `OPENAI_API_KEY` is read from the environment and must not be printed.
- OpenAI Responses API calls send only `model` and `input`.
- The provider input remains the human-editable prompt file plus `RAW_BACKEND_PAYLOAD_JSON` from the raw provider-preview payload.
- Multi-model trials continue after one model fails.
- Optional trial artifacts are written only when `--output-dir` is explicitly provided.

Project/product boundaries:

- Daily Coach Human Voice Prompt Contract v1 is the accepted baseline.
- The human-editable prompt remains user-owned.
- The raw provider-preview payload remains the data source.
- OpenAI/GPT-family output is raw trial evidence only.
- No model is promoted.
- No output is persisted by default.
- No output reaches Today UI.
- No output becomes Daily Coach Note public copy.
- No Daily Next Action behavior changes.
- No API/schema/migration/persistence/report/recommendation behavior changes.
- No OpenAI behavior is enabled outside explicit developer CLI.

Strong non-goals preserved:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior outside explicit developer CLI
```

---
# Current State — Daily Coach Human Voice Prompt Contract v1

Current accepted baseline:

```text
d5bfd29 Merge daily coach provider preview raw data payload v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_d5bfd29_main_merge-daily-coach-provider-preview-raw-data-payload-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Provider Preview Raw Data Payload v1
```

Rejected milestone context:

```text
Daily Coach Provider Preview Runtime Spike v1 was rejected for voice failure.
```

Active backend implementation milestone:

```text
Daily Coach Human Voice Prompt Contract v1
```

Requested status:

```text
DAILY_COACH_HUMAN_VOICE_PROMPT_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Make Daily Coach provider-preview voice iteration human-editable and rerunnable without Python patching.
```

Implemented scope:

- Added a human-editable Daily Coach voice prompt file at `docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md`.
- Added a developer-only terminal preview runner at `tools/dev_daily_coach_human_voice_prompt_preview.py`.
- Added a read-only service that loads the prompt file, passes the prompt text through exactly, appends `RAW_BACKEND_PAYLOAD_JSON`, and calls a provider only when the explicit developer CLI path is used.
- Added a result model that records prompt metadata, payload metadata, raw model output, and safe error metadata.
- Added focused tests for prompt loading, provider input shape, anti-cage prompt contamination rules, raw-output preservation, fake-provider injection, failure metadata, no database mutation from already-built payloads, and terminal output.

Project/product boundaries:

- The user owns final prompt wording.
- Prompt wording can be edited and rerun without Python patching.
- The prompt file is developer-only.
- The preview runner is developer-only and terminal-only.
- The raw provider-preview payload remains the data source.
- The code must not inject backend-authored Daily Coach Note sentence templates.
- The code must not use the old caged Daily Coach Narrative prompt/schema path.
- The code does not parse, validate, score, reject, or approve provider output.
- The code does not persist provider output.
- The code does not change Today UI.
- The code does not change Daily Coach Note public copy.
- The code does not change Daily Next Action.
- The code does not change API/schema/persistence/report/recommendation behavior.
- The code does not promote any model.

Developer-only prompt iteration workflow:

```text
edit docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
run tools/dev_daily_coach_human_voice_prompt_preview.py
inspect terminal output
edit the prompt file again
rerun without patching Python
```

Strong non-goals preserved:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior
```

---
# Current State — Daily Coach Provider Preview Raw Data Payload v1

Current accepted baseline:

```text
e26c4e0 Merge daily coach note copy QA matrix v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_e26c4e0_main_merge-daily-coach-note-copy-qa-matrix-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Copy QA Matrix v1
```

Active backend implementation milestone:

```text
Daily Coach Provider Preview Raw Data Payload v1
```

Requested status:

```text
DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Create a developer-only raw data payload for future Daily Coach Note provider preview from backend-owned deterministic source data.
```

Implemented scope:

- Added `DailyCoachProviderPreviewRawDataPayload` as a developer-only read-only payload model.
- Added a service that builds the provider-preview raw data payload from a `DailyCoachIntelligenceSnapshot` object.
- Added a service path that builds the same payload from a serialized snapshot dictionary.
- Added a convenience service path that builds the payload for `user_id` and `target_date` by first building the existing Daily Coach Intelligence Snapshot.
- Added a developer terminal tool that prints the payload as JSON.
- Preserved raw deterministic source sections under `source_data` instead of collapsing them into a polished paragraph.
- Preserved recovery intelligence, recovery intelligence v2, workout set intelligence, training execution summary, nutrition trend window, foundation layer status, data completeness, source data gaps, reason codes, and limitations where present.
- Added explicit backend truth contract metadata.
- Added explicit provider voice-space metadata that preserves the Uncaged Provider Voice Principle.
- Added provider input guidance that rejects sentence banks, final copy authorization, and normal Today surface authorization.
- Added forbidden provider authority categories for future provider-preview work.

This milestone creates the model's future data pasture.

This milestone preserves the Uncaged Provider Voice Principle.

This milestone gives future provider work raw deterministic backend data, not backend-written sentence banks.

This milestone does not call providers.

This milestone does not generate Daily Coach Note copy.

This milestone does not change Today UI.

This milestone does not change API/schema/persistence/report/recommendation behavior.

This milestone does not change Daily Next Action selection.

This milestone does not add OpenAI/Ollama/CrewAI/RAG/agent behavior.

This milestone does not add model routing or Prompt Lab runtime behavior.

This milestone does not add workout plan, nutrition target, automatic deload, automatic progression, wearable/HRV, or medical interpretation behavior.

Developer-only payload boundaries:

```text
developer_preview_only = true
provider_call_allowed = false
persistence_allowed = false
product_surface_allowed = false
```

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Provider Preview Raw Data Payload work.

---
# Current State — Daily Coach Note Copy QA Matrix v1

Current accepted baseline:

```text
33ebf18 Merge daily coach note recovery-aware language v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_33ebf18_main_merge-daily-coach-note-recovery-aware-language-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Recovery-Aware Language v1
```

Active backend implementation milestone:

```text
Daily Coach Note Copy QA Matrix v1
```

Requested status:

```text
DAILY_COACH_NOTE_COPY_QA_MATRIX_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a focused QA/test/documentation matrix for Daily Coach Note public copy after the first recovery-aware language integration.
```

Expected implementation files:

```text
tests/test_daily_coach_today_card_copy_matrix.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_note_copy_qa_matrix_v1.md
```

Implemented scope:

- Added a focused Daily Coach Note copy QA matrix.
- Covered all approved Daily Next Action classes.
- Covered no-contract, unavailable, limited, low-pressure, moderate-pressure, and high-pressure recovery contract states.
- Verified no-contract Daily Coach Note behavior remains backward compatible.
- Verified recovery contract object input remains valid.
- Verified serialized recovery contract dictionary input remains valid.
- Verified limited/unavailable recovery context uses cautious wording.
- Verified low/moderate/high recovery pressure copy remains bounded.
- Verified public payload does not expose provider/debug/internal contract terminology.
- Verified public payload does not expose unsafe medical, injury, overtraining, automatic deload, automatic progression, or unsafe-to-train claims.
- Verified `coach_note` remains capped at 520 characters.
- Verified Daily Next Action fields are unchanged by recovery copy.
- Verified deterministic public copy remains stable for the same inputs.
- Verified provider calls do not occur in the deterministic Today card matrix path.

This milestone adds QA/test/documentation coverage only.

This milestone does not implement provider behavior.

This milestone does not add OpenAI/Ollama/CrewAI/RAG/agent behavior.

This milestone does not add UI/API/schema/persistence/report/recommendation behavior.

This milestone records the Uncaged Provider Voice Principle for future provider work.

This milestone cages evaluation, not model voice.

Future provider voice should receive raw deterministic backend data, not only backend-written prose summaries.

Repeated-template risk is explicitly recorded as a future provider evaluation concern.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Copy QA Matrix work.

---

# Current State — Daily Coach Note Recovery-Aware Language v1

Current accepted baseline:

```text
c940ff4 Merge recovery-aware coach copy contract v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_c940ff4_main_merge-recovery-aware-coach-copy-contract-v1.zip
```

Latest accepted milestone:

```text
Recovery-Aware Coach Copy Contract v1
```

Active backend implementation milestone:

```text
Daily Coach Note Recovery-Aware Language v1
```

Requested status:

```text
DAILY_COACH_NOTE_RECOVERY_AWARE_LANGUAGE_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Use the accepted Recovery-Aware Coach Copy Contract to add the first bounded, deterministic, user-facing recovery-aware sentence to the Daily Coach Note / Today card path when an approved contract is supplied.
```

Expected implementation files:

```text
services/daily_coach_today_card_service.py
tests/test_daily_coach_today_card_service.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_note_recovery_aware_language_v1.md
```

Implemented scope:

- `build_daily_coach_today_card()` remains backward compatible when no recovery contract is provided.
- The Today card can accept a `RecoveryAwareCoachCopyContract` object or serialized contract dictionary.
- Recovery-aware Today card language is deterministic and contract-bound.
- The Today card may add one short recovery-aware sentence only when the supplied contract supports bounded copy.
- Limited, unavailable, missing, partial, Low-confidence, or Limited-confidence recovery context uses limited-context wording.
- The Today card does not expose provider/debug/internal contract terminology in public text.
- The Today card does not display forbidden recovery-copy language.
- The Today card keeps `coach_note` within the 520-character limit.
- Daily Next Action selection behavior remains unchanged.

This milestone adds the first bounded user-facing Daily Coach Note recovery-aware language.

The language is deterministic and contract-bound.

The language is not provider-generated.

The language does not change Daily Next Action selection.

The language does not add automatic deload/progression behavior.

The language does not add medical interpretation.

The language does not change UI/API/schema/persistence/report/recommendation behavior.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Recovery-Aware Language work.

---

# Current State — Recovery-Aware Coach Copy Contract v1

Current accepted baseline:

```text
66a70d3 Merge daily coach note recovery v2 integration v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_66a70d3_main_merge-daily-coach-note-recovery-v2-integration-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Recovery v2 Integration v1
```

Active backend implementation milestone:

```text
Recovery-Aware Coach Copy Contract v1
```

Requested status:

```text
RECOVERY_AWARE_COACH_COPY_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Create a deterministic, backend-owned copy contract that translates Recovery Intelligence v2 facts into bounded, coach-safe Daily Coach Note copy inputs for future use.
```

Expected implementation files:

```text
models/daily_coach_recovery_copy_models.py
services/daily_coach_recovery_copy_contract_service.py
tests/test_daily_coach_recovery_copy_contract_service.py
docs/project_memory/milestones/recovery_aware_coach_copy_contract_v1.md
```

Scope is limited to a read-only contract/guardrail layer:

- reads existing `recovery_intelligence_v2` from the backend Daily Coach Note context
- returns a structured `RecoveryAwareCoachCopyContract`
- preserves Recovery v2 classification, pressure, confidence, and data-quality status
- lists allowed recovery-aware claim guidance only when supported by Recovery v2 facts
- carries caveats when confidence or data quality is limited, partial, missing, or unavailable
- keeps body weight context bounded and non-causal
- lists forbidden claim categories without authorizing forbidden wording
- serializes through `to_dict()`
- returns a valid limited/unavailable contract when `recovery_intelligence_v2` is missing

This milestone does not expose new user-facing copy.

This milestone does not change Today behavior.

This milestone does not change UI/API/provider/schema/persistence/recommendation/report behavior.

This milestone creates a deterministic copy contract for future use.

No Daily Coach final copy, Today card copy, Streamlit UI, API route, provider, OpenAI/Ollama/CrewAI, RAG/vector/agent, schema/migration, persistence, report, recommendation, workout plan, nutrition target, automatic deload/progression, wearable/HRV, or medical interpretation behavior is authorized by this implementation slice.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Recovery-Aware Coach Copy Contract work.

---

# Current State — Daily Coach Note Recovery v2 Integration v1

Current accepted baseline:

```text
d2e0178 main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_d2e0178_main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
```

Active backend implementation milestone:

```text
Daily Coach Note Recovery v2 Integration v1
```

Requested status:

```text
DAILY_COACH_NOTE_RECOVERY_V2_INTEGRATION_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add Recovery Intelligence v2 additively to the backend-owned Daily Coach Note context layer without changing user-facing Daily Coach copy, Today behavior, UI, API, providers, recommendations, reports, schema, migrations, persistence, or product runtime behavior.
```

Expected implementation files:

```text
models/daily_coach_intelligence_models.py
services/daily_coach_intelligence_snapshot_service.py
tests/test_daily_coach_intelligence_snapshot_service.py
docs/project_memory/milestones/daily_coach_note_recovery_v2_integration_v1.md
```

Scope is limited to exposing structured Recovery Intelligence v2 facts in the existing backend Daily Coach context object:

- preserve existing `recovery_intelligence` v1 field for compatibility
- add optional `recovery_intelligence_v2` field
- source services include `recovery_intelligence_v2_service` when v2 succeeds
- foundation layer status and data completeness record Recovery v2 separately
- source data gaps, reason codes, and limitations record bounded v2 limited/unavailable status
- serialization includes `recovery_intelligence_v2`
- fallback keeps a valid context object if Recovery v2 is unavailable

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing internal code names such as `DailyCoachIntelligenceSnapshot`, `daily_coach_intelligence_snapshot_service.py`, and `snapshot_version` are not broadly renamed in this milestone.

This slice does not add final Daily Coach copy, Today card copy, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, workout plan behavior, nutrition target behavior, or medical interpretation.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Recovery v2 integration work.

---

# Current State — Recovery Intelligence v2 QA Seed Matrix Validation v1

Current accepted baseline:

```text
f50a1cb main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_f50a1cb_main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Product Language Docs Cleanup v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_QA_SEED_MATRIX_VALIDATION_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a terminal-friendly developer/QA seed matrix runner that validates Recovery Intelligence v2 service output across named recovery scenarios before any Daily Coach Note integration is authorized.
```

Expected implementation files:

```text
tools/dev_recovery_intelligence_v2_seed_matrix.py
tests/test_recovery_intelligence_v2_seed_matrix.py
docs/project_memory/milestones/recovery_intelligence_v2_qa_seed_matrix_validation_v1.md
```

Scope is limited to a developer/QA validation artifact that calls the accepted Recovery Intelligence v2 service path:

- named scenario labels
- per-scenario classification, recovery pressure, confidence, data quality, reason codes, limitations, and source facts
- valid JSON-only output for automation and QA parsing
- compact and full terminal-readable output
- optional local `qa-runs/.../qa_report.md` generation for manual QA runs
- focused tests proving the tool uses `build_recovery_intelligence_v2()` instead of duplicating service calculations

The seed matrix is evidence-gathering only. It does not create or mutate seed data, does not add product copy, and does not decide final user-facing recovery voice.

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing code names such as `DailyCoachIntelligenceSnapshot` are not renamed in this milestone.

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, runtime product behavior, or medical interpretation is authorized by this implementation slice.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated recovery intelligence or developer-artifact milestones.

---

# Current State — Recovery Intelligence v2 Developer Artifact / Inspection Tool v1

Current accepted baseline:

```text
09c6581 main_merge-recovery-intelligence-v2-service-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_09c6581_main_merge-recovery-intelligence-v2-service-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Service v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Developer Artifact / Inspection Tool v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_DEV_INSPECTION_TOOL_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a terminal-friendly developer inspection tool that lets Architecture, QA, Backend, and future agents inspect build_recovery_intelligence_v2() output for a user/date before any Daily Coach Note, UI, API, report, recommendation, provider, or schema integration is authorized.
```

Expected implementation files:

```text
tools/dev_recovery_intelligence_v2.py
tests/test_dev_recovery_intelligence_v2_tool.py
docs/project_memory/milestones/recovery_intelligence_v2_dev_inspection_tool_v1.md
```

Scope is limited to a developer artifact that calls the accepted Recovery Intelligence v2 service:

- text inspection output
- valid JSON output from `RecoveryIntelligenceV2Summary.to_dict()`
- compact terminal output
- optional source-fact visibility controls
- focused tests proving the tool uses `build_recovery_intelligence_v2()` instead of duplicating service calculations

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing code names such as `DailyCoachIntelligenceSnapshot` are not renamed in this milestone.

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, or medical interpretation is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated recovery intelligence or developer-artifact milestones.

---

# Current State — Recovery Intelligence v2 Service v1

Current accepted baseline:

```text
dd6db0f main_merge-recovery-intelligence-v2-model-contract-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_dd6db0f_main_merge-recovery-intelligence-v2-model-contract-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Model Contract v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Service v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_SERVICE_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Implement a read-only Recovery Intelligence v2 service that builds the accepted v2 model contract from daily_checkins without changing Daily Coach output, reports, providers, UI, API contracts, schema, migrations, recommendation behavior, or persistence behavior.
```

Expected implementation files:

```text
services/recovery_intelligence_v2_service.py
tests/test_recovery_intelligence_v2_service.py
docs/project_memory/milestones/recovery_intelligence_v2_service_v1.md
```

Scope is limited to constructing the existing `RecoveryIntelligenceV2Summary` model from check-in data:

- preserve `checkin_date` as the primary date
- dedupe duplicate same-day check-ins by latest `created_at` / `id`
- construct current-day context
- construct a 28-day recovery baseline
- construct recent 7-day vs baseline delta
- construct recent 7-day vs prior 7-day delta
- construct indicator-level interpretations for sleep, energy, soreness, body weight, and check-in consistency
- construct data quality, provenance/source facts, confidence, reason codes, limitations, and a coach-safe summary

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, or runtime behavior beyond the new read-only service is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated model-contract or intelligence milestones.

---

# Current State — Recovery Intelligence v2 Model Contract v1

Current accepted baseline:

```text
871d090 main_merge-recovery-intelligence-v2-architecture-planning-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_871d090_main_merge-recovery-intelligence-v2-architecture-planning-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Architecture Planning v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Model Contract v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_MODEL_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add Recovery Intelligence v2 model contracts and tests before any v2 service, Daily Coach Intelligence Snapshot integration, recommendation behavior, provider, API, UI, schema, or persistence changes are authorized.
```

Expected implementation files:

```text
models/recovery_intelligence_v2_models.py
tests/test_recovery_intelligence_v2_models.py
docs/project_memory/milestones/recovery_intelligence_v2_model_contract_v1.md
```

Scope is limited to bounded, serializable model contracts for future Recovery Intelligence v2 concepts:

- current recovery indicator/day context
- recovery baseline
- recent-vs-baseline delta
- recent-vs-prior delta
- indicator-level interpretation
- recovery pressure classification
- readiness classification v2
- data quality
- provenance/source-fact references
- confidence, reason codes, limitations, and coach-safe summary guardrails

No service integration, Daily Coach snapshot integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, or runtime behavior is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated model-contract or intelligence milestones.

---

# Current State — Recovery Intelligence v2 Architecture Planning v1

Current accepted baseline before this docs-only planning slice:

```text
fc7ed70 main_merge-post-north-star-state-reconciliation-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_fc7ed70_main_merge-post-north-star-state-reconciliation-v1.zip
```

Latest accepted milestone:

```text
Post-North-Star State Reconciliation + Architecture/Backend Workflow Memory v1
```

Current Architecture docs-only milestone:

```text
Recovery Intelligence v2 Architecture Planning v1
```

Primary deliverable:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

The Recovery Intelligence v2 plan defines the staged source-data contract direction after v1. It does not authorize runtime behavior changes by itself.

Latest Backend Intelligence Foundation evidence:

- Recovery Intelligence v1 is accepted and merged at `43927d4`.
- Workout Set Intelligence v1 + Daily Coach Intelligence Snapshot v2 is accepted and merged at `123d115`.
- Platform North Star + Future Stack Canonicalization v1 is accepted and merged at `187e433`.
- Post-North-Star State Reconciliation + Architecture/Backend Workflow Memory v1 is accepted and merged at `fc7ed70`.
- Provider voice iteration remains paused.

Next recommended implementation slice after Architecture accepts the plan:

```text
Recovery Intelligence v2 Model Contract v1
```

Purpose of the next implementation slice:

```text
Add Recovery Intelligence v2 model contracts and tests before any v2 service, snapshot integration, recommendation behavior, provider, API, UI, or persistence changes are authorized.
```

No runtime/product behavior changes are authorized by this current state update.

Hard workflow rule now recorded in project memory:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated docs or intelligence milestones.

---

# Current State — Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

Current accepted main:

```text
43927d4 main_merge-daily-coach-intelligence-snapshot-recovery-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_43927d4_main_merge-daily-coach-intelligence-snapshot-recovery-v1.zip
```

Active backend milestone:

```text
Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2
```

Requested status:

```text
DAILY_COACH_WORKOUT_SET_INTELLIGENCE_V1_IMPLEMENTATION_COMPLETE
```

This is the second concrete Backend Intelligence Foundation implementation slice after Recovery Intelligence v1.

Implemented/active scope:

- Workout Set Intelligence v1 as a read-only deterministic set/exercise training indicator layer.
- Daily Coach Intelligence Snapshot v2 with `workout_set_intelligence` included as the richer training source-data layer.
- Existing Training Execution Summary remains in the snapshot for compatibility.
- Existing Recovery Intelligence v1 remains present.
- Existing Nutrition Trend Window remains read-only or recorded as a controlled limitation if unavailable locally.
- Developer-only artifact tool updated to include workout set indicators in JSON, Markdown, pasteback, and `workout_set_intelligence_summary.md`.

Foundation layer status:

```text
recovery_intelligence: implemented_v1
workout_set_intelligence: implemented_v1
trend_engine: nutrition_trend_existing_only
six_month_seed_data: existing_qa_seed_data_only
food_knowledge_expansion: starter_catalog_existing_expansion_pending
```

Provider voice iteration remains paused. This milestone improves backend facts and source-data contracts, not provider prompts.

No user-facing behavior changes are authorized or implemented. Normal Today remains unchanged.

Future next architecture target after acceptance:

```text
Recovery Intelligence v2
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside this milestone.

---

# Current State — Daily Coach Intelligence Snapshot + Recovery Intelligence v1

Current accepted main:

```text
271ac7e main_merge-project-memory-docs-development-architecture-refresh-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-29_271ac7e_main_merge-project-memory-docs-development-architecture-refresh-v1.zip
```

Active backend milestone:

```text
Daily Coach Intelligence Snapshot + Recovery Intelligence v1
```

Requested status:

```text
DAILY_COACH_INTELLIGENCE_SNAPSHOT_RECOVERY_V1_IMPLEMENTATION_COMPLETE
```

This is the first concrete Backend Intelligence Foundation implementation slice after the docs/process/development architecture refresh.

Implemented/active scope:

- Recovery Intelligence v1 as a read-only deterministic layer over `daily_checkins`.
- Daily Coach Intelligence Snapshot v1 as a read-only backend-owned source-data contract.
- Existing Training Execution Summary is included read-only.
- Existing Nutrition Trend Window is included read-only or recorded as a controlled limitation if unavailable locally.
- Developer-only artifact tool: `tools/dev_daily_coach_intelligence_snapshot.py`.

Foundation layer status:

```text
recovery_intelligence: implemented_v1
workout_set_intelligence: existing_training_execution_summary_only
trend_engine: nutrition_trend_existing_only
six_month_seed_data: existing_qa_seed_data_only
food_knowledge_expansion: starter_catalog_existing_expansion_pending
```

Provider voice iteration remains paused. This milestone improves backend facts and source-data contracts, not provider prompts.

No user-facing behavior changes are authorized or implemented. Normal Today remains unchanged.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside this milestone.

---

# Current State — Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1

Current accepted main:

```text
23b5378 Merge daily coach fully free source-data lab evidence v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-29_23b5378_main_merge-daily-coach-fully-free-source-data-lab-evidence-v1.zip
```

Latest Daily Coach provider evidence:

- v4 free-range prompt/payload decaging is accepted as a developer-only diagnostic baseline at `56d63c4`.
- Fully Free Source-Data Lab v1 is merged as developer-only evidence at `23b5378`.
- Fully Free v1 was technically valid and useful as evidence, but it was not meaningfully better than v4.
- Outputs were competent but generic and structurally repetitive.
- Provider voice iteration is paused.

Active milestone:

```text
Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1
```

Requested status:

```text
PROJECT_MEMORY_HANDOFF_COMPRESSION_STALE_DOCS_DEVELOPMENT_ARCHITECTURE_V1_IMPLEMENTATION_COMPLETE
```

Owner:

```text
Backend Development, as routed by Architecture for a docs-only repo patch.
```

Next product architecture center after this docs milestone:

```text
Daily Coach Backend Intelligence Foundation
```

Foundation layers:

- Recovery Intelligence
- Workout Set Intelligence
- Trend Engine
- Six-Month Seed Data
- Food Knowledge Expansion

Sequencing principle:

```text
Build the product brain first. Then build the fancy nervous system.
```

No serious RAG, vector search, embeddings, multi-agent orchestration, LangGraph, CrewAI, LlamaIndex, or production-grade agent architecture should proceed until these backend intelligence layers are designed and robust enough to feed them.

Canonical seven visible team/chat lanes:

1. Architecture
2. Backend Development
3. QA
4. Agent Engineering
5. Streamlit UI / UX
6. Portfolio Packaging
7. DevOps & Tooling

Project Memory / All Future Agents is not one of the seven visible team/chat lanes. It is a repo continuity concern that every team must respect.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated milestones.

## Active docs-only non-goals

This milestone does not authorize runtime behavior changes, provider behavior changes, OpenAI default changes, Today provider display, Streamlit UI changes, API/schema/migration changes, RAG, embeddings, pgvector, vector DB setup, LangGraph, CrewAI, LlamaIndex, multi-agent runtime, custom GPT build, recovery intelligence implementation, workout set intelligence implementation, trend engine implementation, six-month seed data generation, food catalog expansion, provider prompt experiments, or reviewer/renderer implementation.

## Historical current-state notes

The sections below are retained for history only. The active state is the `23b5378` docs refresh state above.

# Current State — Daily Coach Fully Free Source-Data Lab v1

Current source of truth: `main` at `56d63c4 Merge daily coach free-range decaging diagnostic baseline v4`.

Active backend milestone: `Daily Coach Fully Free Source-Data Lab v1`.

Status: Architecture merged and snapshotted the free-range decaging v4 diagnostic baseline, then routed Backend to build a separate developer-only source-data lab from `main`, not from the unmerged feature chain.

Purpose: test whether GPT-5.5 can produce a meaningfully better Daily Coach note when it receives clean, organized source data and almost no coaching cage. This is a single-model lab, not multi-agent orchestration, RAG, embeddings, vector search, production provider enablement, or normal Today replacement.

Implementation direction: add a separate developer-only lab tool, build `fully_free_source_data_packet` artifacts, use a minimal prompt, support fully free prompt variants, capture exact first-pass drafts, and add post-hoc audits for source-data completeness, model freedom, backend-prose contamination, completion diagnostics, claim risk, artifact safety, and token/cost telemetry.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

Current source of truth: `feature/daily-coach-free-range-voice-precision-payload-enrichment-v2` at `d731a6c Enrich free range voice precision payload`.

Active backend milestone: `Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3`.

Status: Architecture classified v2 as a promising partial with product signal, but found truncation, raw-number formatting leaks, thin food context, and one targeted regression. Backend is continuing the developer-only free-range experiment from the unmerged v2 feature branch, not `main`.

Purpose: improve output completion, display-ready numeric surfaces, macro/food card artifacts, AI snack candidates, bounded food seeding, weight-anomaly handling, workout/session naming visibility, and voice-style diagnostics while preserving the full first-pass coach note.

Implementation direction: keep first-pass drafts exact and unmodified; keep diagnostics post-hoc only; fix deterministic provider live-opt-in regression; add completion diagnostics; expand practical food candidates; add food option/macro display cards, AI snack candidates, number-formatting and voice-style summaries; preserve provider-input debug and model-input manifest artifacts.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Free-Range Voice + Precision + Payload Enrichment v2

Current source of truth: `feature/daily-coach-full-user-day-free-range-payload-baseline-v1` at `eb26c59 Add daily coach full user-day free-range trial`.

Active backend milestone: `Daily Coach Free-Range Voice + Precision + Payload Enrichment v2`.

Status: Architecture accepted the v1 free-range thesis as materially better but requested one more developer-only iteration before merge/product-renderer work. Backend is enriching the free-range path with voice variants, precision metadata, broader inspectable food context, set-level data availability reporting, and stronger model-input manifest artifacts.

Purpose: determine whether GPT-5.5 continues improving when it receives a broad neutral full user-day packet with clearer precision/quote metadata, more useful food candidate structure, multiple coach voices, and exact provider-input inspection.

Implementation direction: keep the full coach note intact, preserve exact first-pass draft capture, add strict/empathetic/hypeman coach variants, expose food/macro precision and quote style, make model input inspectable through `model_input_manifest.md`, summarize food candidates and precision, and keep all audits post-hoc only.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_VOICE_PRECISION_PAYLOAD_ENRICHMENT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Full User-Day Free-Range Payload Baseline v1

Current source of truth: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Active backend milestone: `Daily Coach Full User-Day Free-Range Payload Baseline v1`.

Status: Architecture stopped the phrase-cleanup loop after provider payload forensics showed GPT-5.5 still received app/deterministic prose through the rendered prompt. Backend is implementing a developer-only free-range payload baseline from the last accepted main snapshot, not from the failed v2 branch.

Purpose: answer whether GPT-5.5 can write a genuinely useful Daily Coach note when given a broad neutral structured user-day packet instead of app-generated coach prose, deterministic fallback copy, phrase bans, repair context, or Product Voice Audit scaffolding.

Implementation direction: build a `DailyCoachFullUserDayPacket`, render it as provider-visible data, support minimal/practical/direct free-range prompt variants, support repeated runs, capture exact first-pass drafts before any post-hoc diagnostics, and add opt-in provider payload debug artifacts (`provider_input_prompt.md` and `provider_payload_debug.json`).

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULL_USER_DAY_FREE_RANGE_PAYLOAD_BASELINE_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Wide Context Copy Cleanup + QA Readability v1

Current source of truth: `main` at `42d0bd4 Merge daily coach wide context ceiling trial v1`.

Active backend milestone: `Daily Coach Wide Context Copy Cleanup + QA Readability v1`.

Status: Backend implementation patch is ready for local validation after Architecture routed the merged wide-context ceiling-trial baseline back for a narrow copy/readability patch. Live QA classified the prior result as `CONTEXT_HELPED_BUT_NOT_ENOUGH`.

Purpose: keep the wide-context ceiling-trial architecture, but clean backend-shaped wording from prompt/context packaging and make QA artifacts easier to inspect from the terminal. This remains developer-only. It is not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit/fallback-gate milestone.

Implementation direction: preserve backend truth and safety boundaries while making writer-facing context more human-facing; avoid wording such as `Nutrition is lagging`, `approved option`, `gap is still open`, and `planned workout as written`; add terminal-friendly compact artifacts, product-language findings, best-variant summary, and pasteback report support.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614/42d0bd4 lineage, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated milestones unless directly scoped.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_COPY_CLEANUP_QA_READABILITY_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

Current source of truth: `main` at `718c614 Merge daily coach product voice audit gate fix v1`.

Active backend milestone: `Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1`.

Status: Architecture accepted Backend Continuation Onboarding and directed Backend to proceed with the ceiling trial. Backend implementation is complete and ready for Architecture / QA review.

Purpose: answer whether GPT-5.5 can write genuinely better Daily Coach copy when given richer backend-approved context and fewer pre-draft writing shackles. This is a developer-only ceiling trial, not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit phrase patch.

Implementation direction: wide context packet builder, minimal writer prompt variants, exact first-pass draft capture, side-by-side comparison against deterministic and current narrow path, token/cost telemetry fields, sanitized artifacts, QA scoring template, and baseline drift documentation.

Known baseline drift documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614 snapshot, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside the ceiling trial unless it directly blocks targeted validation. Full-suite green must not be claimed if this drift remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_UNCAGED_GPT55_CEILING_TRIAL_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1

Current source of truth: `feature/daily-coach-natural-draft-product-voice-audit-v2` at `9ba9579 Add daily coach natural draft product voice audit v2`.

Active backend patch: `Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1`.

Status: Architecture routed v2 back to Backend for a focused approval-gate and audit-calibration patch.

QA found v2 architecture is useful as a diagnostic system, but final approval was wrong: failed fallback could still become final approved copy, Product Voice Audit was too lenient, food-action language was incomplete, and repair gave up too early when first-pass copy only needed light wording cleanup.

Patch direction: keep the writer loose, sharpen the reviewer, prefer light product-voice repair over fallback when factual claims are safe, and block final approval when fallback itself fails Product Voice Audit.

Required status: `DAILY_COACH_PRODUCT_VOICE_AUDIT_CALIBRATION_FINAL_APPROVAL_GATE_FIX_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Natural Draft + Product Voice Audit v2

Current source of truth: `main` at `4104796 Merge daily coach natural draft claim audit v1`.

Active backend milestone: `Daily Coach Natural Draft + Product Voice Audit v2`.

Status: Architecture approved for Backend implementation.

Natural Draft + Claim Audit v1 is merged as developer infrastructure but QA found it was only a technical partial: the factual reviewer existed, but product-quality review did not. V2 extends that path with first-pass model draft visibility, Product Voice Audit, food-action language checks, side-by-side comparison, repair delta reporting, humanized fallback, final approval gates, and reviewer conclusions.

Core principle: loosen the writer, tighten the reviewer, expose the first draft, and compare honestly. Deterministic fallback is the floor, not the goal.

V2 remains developer-only. Normal Today behavior is unchanged. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Backend remains final authority for facts, claim audit, product voice audit, repair limits, fallback, and final approval.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Natural Draft + Claim Audit v1

Current source of truth: `main` at `b9b46c9 Merge daily coach prompt lab voice lab v1`.

Active backend milestone: `Daily Coach Natural Draft + Claim Audit v1`.

Status: Architecture approved for Backend implementation.

Prompt Lab / Voice Lab v1 is merged as technical developer tooling, but product strategy has pivoted to Natural Draft + Claim Audit. The active architecture is: backend-approved coach brief → natural coach draft → deterministic claim extraction → backend claim audit → one targeted repair attempt → final approved copy or deterministic fallback.

Core principle: loosen the writer, tighten the reviewer. GPT-5.5 may draft naturally from a clean `ApprovedCoachBrief`, but Backend remains final authority for facts, interpretations, claim audit, repair limits, fallback, and final approval.

Boundaries remain unchanged: developer-only path; normal Today behavior unchanged; deterministic remains default; OpenAI/direct_ollama remain explicit opt-in/evaluation-only; no provider promotion; no public UI; no provider output persistence; no parser/validation/fallback relaxation; no raw DB access for provider; no RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, or queue changes.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_CLAIM_AUDIT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Prompt Lab / Voice Lab v1

Current source of truth: `main` at `2835d09 Merge daily coach plainspoken voice action clarity v5`.

Active backend milestone: `Daily Coach Provider Prompt Lab / Voice Lab v1`.

Status: Architecture approved for Backend implementation.

V5 technically passed infrastructure but failed product voice. The current milestone is developer-only Prompt Lab / Voice Lab tooling, not another one-off phrase-hardening patch.

The lab compares fixed scenario cases and prompt/context variants through the existing Daily Coach provider path, parser, validator, fallback boundary, sanitized artifacts, and manual scoring template.

Deterministic remains default. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Normal Today behavior, product persistence, Streamlit provider controls, parser rules, quote/value validation, and fallback behavior remain unchanged.

Requested final status: `DAILY_COACH_PROVIDER_PROMPT_LAB_VOICE_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Plainspoken Voice & Action Clarity v5

Current source of truth: `feature/daily-coach-provider-human-voice-food-action-specificity-v4` at `0ace3da`.

Active backend milestone: `Daily Coach Provider Plainspoken Voice & Action Clarity v5`.

Architecture status: approved for Backend implementation after the green v4 baseline snapshot.

Status: backend implementation patch ready for local validation.

V5 replaces phrase-ban-only tuning with a plainspoken coaching contract. The Daily Coach should say the actual action, use friendly food labels, explain the food reason, connect recovery to training behavior, and keep the priority action concrete without motivational packaging or backend/framework language.

Implemented direction:

- plainspoken voice contract and rejected phrase registry;
- `food_action_context` with friendly food options, macro reason, and backed food-action sentence patterns;
- prompt rewrite around plain examples and anti-examples;
- stronger visible-output validation for user-rejected phrases, canonical food leakage, unbacked food action, invented timing, invented pairings, and invented serving labels;
- trial-matrix v5 diagnostics for plainspoken phrase flags, food-gap reason use, food condition use, slogan-like phrases, and manual product voice scoring.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_PLAINSPOKEN_VOICE_ACTION_CLARITY_V5_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3

Current source of truth: `feature/daily-coach-context-selection-coaching-synthesis-v2` at `2cd7708`.

Active backend milestone: `Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3`.

Architecture status: approved for Backend implementation.

Status: backend implementation patch ready for local validation.

V3 addresses product-copy quality after v2 technical pass by giving providers a more natural, human-readable, claim-backed context starter while preserving strict backend truth boundaries. The implementation adds `approved_context_brief`, `claim_backing_map`, cleaned today_story phrasing, natural voice examples/anti-examples, explicit `verbosity_budget`, hard/diagnostic phrase checks, and v3 trial-matrix diagnostics.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_VOICE_CONTEXT_FREEDOM_RICH_SYNTHESIS_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Context Selection & Coaching Synthesis v2

Current source of truth: accepted copy-grounding branch baseline at `2bbffdb`.

Active backend milestone: `Daily Coach Provider Context Selection & Coaching Synthesis v2`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone improves provider context selection and coaching synthesis by adding deterministic `today_story`, expanded high-value claim selection, field-specific claim budgets, adaptive verbosity guidance, prompt synthesis framing, and v2 trial-matrix diagnostics.

Adaptive verbosity rule: the target is useful, grounded, scannable coaching, not maximum brevity. More words are allowed only when approved context is rich and the extra words improve actionability, connect multiple domains, or explain food/training/recovery context clearly. Shorter copy is required when context is sparse, generic, report-like, repetitive, or unsupported.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_CONTEXT_SELECTION_COACHING_SYNTHESIS_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

Current source of truth: `main` / accepted runtime-fix baseline at `60fe77b`.

Active backend milestone: `Daily Coach Provider Copy Grounding & Approved Context Enrichment v1`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone enriches provider-approved context packaging and prompt guidance so OpenAI can write more specific Daily Coach copy without weakening the existing parser, quote/value validator, fallback path, or deterministic default.

Implemented direction:

- approved value claim metadata: `priority`, `section_hint`, `coaching_use`, `display_hint`, `value_style`;
- provider context packaging: `provider_task_context`, `high_value_claims`, `preferred_claims_by_field`, `claim_usage_rules`, `field_role_guidance`;
- prompt/field-role guidance for practical coach copy using 2-4 high-value claims;
- trial-matrix copy-quality diagnostics and manual review placeholders.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_COPY_GROUNDING_APPROVED_CONTEXT_ENRICHMENT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State — Daily Coach Provider Trial Diagnostics v1

Current source of truth: `main` at `a6cd8d0` plus accepted Daily Coach Narrative Provider Trial Matrix tooling at `4641c91`.

Active backend milestone: `Daily Coach Provider Trial Diagnostics v1`.

Status: Architecture approved for Backend implementation.

Diagnostics v1 improves the provider trial matrix only. It adds explicit local raw-provider-output diagnostics, safer OpenAI configuration/error classification, safe provider config metadata, optional Ollama unload cleanup, and artifact-safety guardrails.

Deterministic remains default. `direct_ollama` and `openai` remain opt-in. No product runtime, Streamlit, persistence, parser, validator, quote/value, nutrition, workout, recovery, or report behavior changes are authorized.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

---

# Current State Update — Daily Coach Narrative Provider Trial Matrix v1

Current source of truth: `main`.

Required source main commit: `a6cd8d0`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_a6cd8d0_daily-coach-narrative-approved-value-quote-validation-v1.zip`.

Previous accepted statuses:

- `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED_AND_MERGED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_QA_V1_PASS`

Current backend milestone: Daily Coach Narrative Provider Trial Matrix v1.

Branch: `feature/daily-coach-narrative-provider-trial-matrix-v1`.

Commit-check mode: code.

QA class: CLASS 2 / CLASS 5 HYBRID.

Status: backend implementation in progress.

Requested final status: `DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.

## Goal

Add repeatable provider trial matrix tooling for Daily Coach value-aware narratives.

The tool compares the same approved Daily Coach contexts across:

- deterministic;
- direct_ollama;
- openai.

The matrix records schema adherence, parse/validation/fallback behavior, quote/value discipline, latency, approved narrative output, rendered narrative output, and manual-review placeholders without changing runtime defaults.

## Implemented direction

Provider evaluation must run through the accepted Daily Coach value-aware narrative path and approved value quote validation path.

Live providers are skipped unless explicitly enabled with `--allow-live-providers`.

Generated artifacts must not include raw provider output or secrets.

The normal app/runtime behavior remains unchanged.

## Scope boundaries

Deterministic remains default.

`direct_ollama` remains opt-in offline/developer mode.

`openai` remains opt-in hosted comparison provider.

No provider default change is authorized.

No live provider calls are allowed in automated tests.

No Streamlit provider controls are added.

No provider narratives are persisted.

No parser, validator, quote/value, nutrition, workout, recovery, report, schema, or persistence behavior is changed.

No snapshots are committed.

## Architecture review step

Return to Architecture after implementation and validation.

Requested final status:

`DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.


## Historical continuity anchors — reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- Provider Narrative QA Matrix v2
- Daily Coach Async Service Shell / No Worker v1
- Daily Coach Async Provider Runtime Design v1
- qwen3:32b research / future premium async candidate only
- deterministic fallback remains mandatory
- Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries
- AI explains backend-approved truth
- no provider on normal Today page load unless explicitly configured

## Historical continuity anchors — additional reference-only preservation

These phrases are preserved to avoid losing accepted historical continuity context:

- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- No provider may run on normal Today page load
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- service shell only
- no provider execution added


---

# Current Implementation Update — Daily Coach Provider Human Voice & Food Action Specificity v4

Status: Backend v4 patch candidate built from v3 baseline `e23a435`.

This milestone addresses the v3 product-copy failure after technical validation passed. It improves provider-facing human voice and food action specificity while preserving strict backend truth boundaries.

Implemented direction:

- friendly food labels are generated for provider/user-facing copy;
- canonical food labels remain traceability/debug context;
- serving display remains conservative and backend-approved only;
- nutrition_action_context explains the approved food action without letting the model invent meal plans;
- claim_backing_map separates internal meaning from user-facing phrase examples;
- approved_context_brief and today_story avoid known awkward framework phrases;
- prompt examples now directly ban the phrases rejected in QA/user critique;
- validation catches canonical food label leakage, unquoted friendly foods, invented serving wording, and repeatedly rejected phrases;
- trial matrix diagnostics include v4 food/voice fields.

Boundaries preserved:

- deterministic default unchanged;
- OpenAI/direct_ollama opt-in only;
- parser and quote/value validation remain strict;
- no provider persistence;
- no Streamlit changes;
- no nutrition target, workout, recovery, or report architecture changes.


---

# Current Implementation Update — Daily Coach Free-Range Prompt + Payload Decaging v4

Status: Backend v4 patch candidate built from v3 baseline `c36c50a`.

This milestone continues the unmerged free-range Daily Coach experiment and addresses the v3 finding that the coach output was still too backend-bound. The implementation splits internal/debug payloads from the model-facing coach-facts surface, decages the provider prompt when explicitly requested, and adds direct/hypeman-clean variants while preserving exact first-pass output and post-hoc-only diagnostics.

Implemented direction:

- deterministic provider remains runnable without `--allow-live-provider` while OpenAI/direct_ollama remain explicit opt-in;
- debug payloads may retain backend/internal fields, but `model_facing_coach_facts.md/json` exposes cleaner coaching source material;
- `--prefer-decaged-prompt` uses `MODEL_FACING_COACH_FACTS_JSON` instead of the full backend-shaped packet;
- the decaged prompt tells GPT-5.5 not to echo field labels/internal categories and to use editorial judgment;
- the prompt specifically discourages main-note numeric overload, panic-level macro deficit framing, Markdown bold, emoji headers, decorative Markdown, and repeated `roughly` wording;
- direct/hypeman-oriented clean variants were added for the v4 voice matrix;
- completion diagnostics now report expected/captured/complete/truncated/skipped counts;
- food/snack formatting aggregates mini-meal macros before display;
- new artifacts include model-facing coach facts, decaging summary, and backend label exposure summary;
- provider payload debug includes both debug packet and model-facing facts so Architecture/QA can inspect the split.

Boundaries preserved:

- developer-only experiment;
- normal Today unchanged;
- no production Today replacement;
- no restrictive renderer/reviewer gate;
- no OpenAI default or provider promotion;
- no public UI or Streamlit controls;
- no raw provider envelope persistence, secrets, or raw DB dumps;
- no medical advice generation;
- no meal planning, workout generation, nutrition target, recovery score, RAG, embeddings, multi-agent runtime, Headroom/context compression, local/cheaper model comparison, or full 450–500 food expansion.
