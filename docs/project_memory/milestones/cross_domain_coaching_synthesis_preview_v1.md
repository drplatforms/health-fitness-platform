# Cross-Domain Coaching Synthesis Preview v1

## Status

```text
CROSS_DOMAIN_COACHING_SYNTHESIS_PREVIEW_V1_ACCEPTED_MERGED_AND_CLOSED
```

## Accepted Git State

- Accepted merge: `b63ec69 Merge semantic cross-domain coaching preview`.
- Feature implementation: `596f14b Add semantic cross-domain coaching preview`.
- Implementation base: `main` at `9c5ae0f Merge manifest-aware canonical food promotion`.
- The feature is merged on `main`; final docs-only closeout and snapshot hashes are authoritative in Git after this memory update.

## Scope

- Developer-only backend/CLI preview.
- No Today/public UI, public API route, normal provider runtime, persistence, schema, migration, dependency, frontend change, or provider promotion.
- Backend remains authoritative for facts, constraints, semantic action availability, deterministic resolution, confidence, validation, and fallback.
- Providers produce a structured specialist assessment and user-facing narrative wording only.
- Successful execution uses at most two provider calls. There are no repair, retry, debate, agent-framework, or third-call paths.

## Accepted Semantic Contract

- `ApprovedActionCatalogItem`, `CrossDomainSelectableAction`, and `ResolvedCoachingAction` contain semantic identity and typed parameters rather than user-facing `text`.
- Recovery maps to `maintain_planned_training`; training maps to `execute_planned_session` with RIR values taken from approved claim data; nutrition maps to `consider_food_candidate` with approved food data and explicit serving permission.
- Legacy `instruction`, `interpretation`, `allowed_phrasings`, and `blocked_phrasings` are neither copied nor parsed by the cross-domain adapter.
- Limitations and source gaps are normalized into bounded semantic conditions. They are not selectable actions and no conservative fallback sentence is inserted into the provider contract.
- The complete `CrossDomainEvidencePacket` remains the audit/provenance artifact.
- The provider-facing assessment projection remains capped at recovery/nutrition/training/shared `8/8/10/5` (`31` total) and excludes metadata, row-level noise, summaries, coach-safe prose, recommendations, desired coaching moves, today intent, recommended focus, and limitation/source-gap sentences.
- The raw `ApprovedCoachBrief` does not enter the narrative call.
- `cross_domain_semantic_narrative_context_v1` contains scenario, deterministic semantic decisions, typed domain status, bounded relevant approved facts, confidence conditions, and forbidden-topic codes.
- Narrative facts remain capped at recovery `6`, nutrition `8`, and training `6`.
- The narrative provider does not receive today-intent copy, approved interpretation copy, training/recovery instruction copy, phrasing banks, specialist observations, coach-safe summaries, deterministic fallback prose, or the backend certainty phrase list.
- The narrative prompt contains no sample coaching sentences and requires only strict `headline`/`body` JSON.

## Validation And Safety

- Audit order remains claim audit, confidence-coherence audit, product-voice audit, then approval.
- Unsupported foods, servings, timing, macro values, workout changes, causal claims, certainty escalation, and source-gap denial remain rejected.
- Invalid assessment output blocks the narrative call.
- Direct Ollama uses the existing lifecycle and structured-output helpers. Qwen3 payloads set `think: false`; Qwen2.5 behavior is unchanged.
- Optional output includes `semantic_narrative_context.json` plus the existing evidence, assessment, provider-input, resolution, and audit artifacts. No artifacts are written without `--output-dir`.
- Merged-main targeted provider/audit regression: `136 passed`.
- Merged-main project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`.
- Merged-main project-memory tests: `29 passed`.
- Ruff check: passed.
- Ruff format check: passed.
- `git diff --check`: passed.
- No browser smoke was required because the milestone is developer-only and changed no UI, public API, or normal runtime behavior.

## Live Provider Findings

Frozen benchmark:

```text
user: 102
date: 2026-05-31
scenario: aligned_managed
```

Findings:

- Earlier sentence-driven Qwen2.5:3B and Qwen3:8B trials demonstrated that backend-authored action prose caused template assembly and mechanical writing.
- After the semantic-contract correction, Qwen3:8B and Qwen3:32B produced genuinely new wording rather than copying the removed legacy sentences.
- The semantic contract therefore succeeded as infrastructure.
- Narrative quality still failed product acceptance. Both post-correction models produced familiar generic health-coach language and followed an editorial outline already determined by backend-selected primary and supporting actions.
- The remaining limitation is editorial freedom, not direct prose leakage: the provider may choose wording but does not yet choose the most useful focus or whether supporting domains deserve inclusion.
- The product-voice audit returned overly generous readiness scores for mediocre prose and is not trusted as a product-readiness signal for this workflow.
- The OpenAI upper-bound benchmark is deferred to avoid spending credits before the editorial contract is corrected.

## Accepted Verdict

```text
SEMANTIC_PROVIDER_CONTRACT_ACCEPTED
NARRATIVE_PRODUCT_QUALITY_NOT_ACCEPTED
OPENAI_BENCHMARK_DEFERRED
```

This milestone is accepted, merged, and closed as infrastructure. It does not authorize Today/public/provider promotion.

## Next Direction

Next milestone:

```text
Cross-Domain Narrative Decision Freedom v1
```

The backend should provide a safe candidate decision envelope containing approved facts, candidate semantic actions, conflicts, vetoes, confidence, and mandatory safety constraints.

The narrative provider should be allowed to:

- choose the most useful primary focus;
- choose zero, one, or two approved supporting ideas;
- omit irrelevant domains;
- return selected semantic action keys alongside `headline` and `body`.

The backend should validate those selected keys, factual claims, foods, values, and safety constraints without predetermining the narrative outline.

Separate later work:

```text
Canonical Food Candidate Expansion for Coaching v1
```

That milestone should retrieve and rank a broader, diverse candidate pool from the canonical catalog instead of sending the full catalog or repeatedly exposing only the current narrow food set.

## Non-Goals Preserved

- No normal Today behavior, public API, persistence, schema, dependency, runtime default, provider promotion, nutrition target, workout generation/progression, recovery calculation, food catalog mutation, canonical promotion, USDA pipeline, or real database changed.
- No CrewAI, LangChain, RAG, embeddings, fuzzy matching, repair call, retry, or third provider call was added.
