# Cross-Domain Coaching Synthesis Preview v1

## Status

```text
READY_FOR_ARCHITECTURE_SEMANTIC_CONTRACT_REVIEW
```

## Base And Scope

- Accepted base: `main` at `9c5ae0f Merge manifest-aware canonical food promotion`.
- Implementation branch: `feature/cross-domain-coaching-synthesis-preview-v1`.
- This is a developer-only backend/CLI preview. It adds no Today/public UI, API route, normal provider runtime, persistence, schema, migration, dependency, frontend, or provider promotion.
- Backend remains authoritative for facts, constraints, semantic action availability, deterministic resolution, confidence, validation, and fallback. Providers write candidate assessment observations and narrative wording only.

## Semantic Contract

- `ApprovedActionCatalogItem`, `CrossDomainSelectableAction`, and `ResolvedCoachingAction` contain semantic identity and parameters, not user-facing `text`.
- Recovery actions map the approved recovery collection to `maintain_planned_training` with no intensity change and no max-effort test. Training actions map to `execute_planned_session`; their RIR range is read from approved claim data, never parsed from legacy instruction prose. Nutrition actions expose the approved food name, macro reason, and serving only when serving display is explicitly allowed.
- Legacy `instruction`, `interpretation`, `allowed_phrasings`, and `blocked_phrasings` fields are neither copied nor parsed by the cross-domain adapter. Mutating that prose does not change semantic actions.
- Limitations and source gaps are normalized into bounded semantic `code`/`scope`/`status` conditions. They are not selectable actions and no conservative fallback sentence is inserted into the resolved provider contract.

## Assessment Boundary

- The complete `CrossDomainEvidencePacket` remains the audit/provenance artifact and may retain source text for developer inspection.
- `CrossDomainAssessmentContext` is the provider-only projection. It keeps recovery/nutrition/training/shared caps of `8/8/10/5` (`31` total), uses explicit typed-field allowlists, and emits evidence ID, domain, semantic fact key, typed value, safe display value, and confidence.
- Metadata, trend-day rows, exercise/session rows, summaries, coach-safe summaries, interpretations, recommendations, desired coaching moves, today intent, recommended focus, reason-code prose, and limitation/source-gap sentences are excluded.
- Selectable actions expose `action_key`, domain, `action_type`, parameters, and only user-facing approved supporting claims from `ApprovedCoachBrief.claim_registry`. Dynamic assessment schemas still constrain exact evidence IDs and domain-owned action keys.
- Specialist observation text and tension summaries remain developer inspection data and do not enter the narrative call.

## Narrative Boundary

- The raw `ApprovedCoachBrief` no longer enters the narrative provider input.
- `cross_domain_semantic_narrative_context_v1` contains the scenario, deterministic primary/supporting/suppressed semantic actions, resolution reason codes, typed domain assessment status, bounded relevant approved facts, semantic confidence/condition data, and forbidden-topic codes.
- Narrative facts are capped at recovery `6`, nutrition `8`, and training `6`. Existing claim taxonomy and semantic key shapes admit approved statuses, names, numbers, ranges, and trends while excluding context/limitation claims and prose-bearing keys.
- The provider does not receive today-intent copy, approved interpretation copy, training/recovery instruction copy, phrasing banks, coach-safe summaries, fallback copy, specialist prose, or the backend forbidden-certainty phrase list.
- The narrative prompt gives no sample wording. It asks the provider to write every user-facing sentence from semantic facts and decisions while preserving strict `headline`/`body` JSON.

## Validation And Audits

- Audit order remains claim audit, confidence-coherence audit, product-voice audit, then approval. No audit requires sentence similarity to legacy backend copy.
- Unsupported foods, servings, timing, macro values, workout changes, causal claims, certainty escalation, and source-gap denial remain rejected. Provider output can use wholly new wording when its claims remain supported.
- Successful previews still make exactly two provider calls. Invalid assessment output blocks the narrative call. There are no repair, retry, debate, agent-framework, or third-call paths.
- Direct Ollama still uses the existing lifecycle and structured-output helpers. Qwen3 payloads set `think: false`; Qwen2.5 behavior is unchanged. Automated tests inject providers and make no live call.
- Optional output now includes `semantic_narrative_context.json`, containing exactly the structured narrative context without its prompt wrapper. Existing evidence, assessment-context, provider-input, resolution, and audit artifacts remain. No output is written without `--output-dir`.

Completed checks:

- Focused semantic-contract preview tests: `96 passed`.
- Required eight-file provider/audit regression slice: `136 passed`.
- Ruff check: passed for all five touched Python files.
- Ruff format check: passed for all five touched Python files.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`.
- Project-memory checker tests: `29 passed`.
- `git diff --check`: passed.
- No live provider call, full suite, browser smoke, frontend build, or database access was performed.

## Architecture Gate

Architecture must inspect the actual generated assessment and narrative provider inputs before another live model run. Runtime testing remains blocked if either provider can see backend-authored coaching sentences or phrasing banks, if the narrative provider can see the raw `ApprovedCoachBrief`, or if resolved actions carry copy instead of semantics.

The next authorized live comparison remains the frozen `user 102`, `2026-05-31`, `aligned_managed` benchmark with `direct_ollama / qwen3:8b` for both calls. This milestone does not authorize that run.

Product-voice scoring remains a known follow-up. It was not redesigned or weakened in this correction.

## Non-Goals Preserved

- No normal Today behavior, public API, persistence, schema, dependency, runtime default, provider promotion, nutrition target, workout generation/progression, recovery calculation, food catalog, canonical promotion, USDA pipeline, or real database changed.
- No CrewAI, LangChain, RAG, embeddings, fuzzy matching, repair call, retry, or third provider call was added.
- Nothing was staged, committed, pushed, merged, or snapshotted.
