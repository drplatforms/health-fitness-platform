# Direct Ollama Training Report Section Provider v1

## Status

Promoted as the opt-in provider boundary after Training Evidence Claim Runtime QA v1.

Runtime QA accepted the known-good path as FULL PASS for:

- user_id: 102
- date: 2026-06-06
- model: `ollama/qwen2.5:3b`
- run count: 2
- validation status: approved
- fallback used: false

No parser relaxation, validator relaxation, fallback bypass, or code rollback was required.

## Provider configuration

Deterministic remains the default. Direct Ollama remains opt-in.

```text
TRAINING_REPORT_SECTION_PROVIDER=deterministic|direct_ollama
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
```

`ollama/qwen2.5:3b` is the supported Provider Promotion v1 model. Other local models, including qwen3 variants, remain experimental/product-voice probes only and must pass the same parser, validator, exact-anchor, and fallback contract before support is considered.

## Accepted architecture

The accepted provider flow is:

```text
approved workout/training facts
→ TrainingEvidenceContext
→ ApprovedTrainingClaim[]
→ model-facing quote context
→ direct Ollama candidate
→ strict JSON parser
→ exact-anchor validator
→ provider-approved section or deterministic fallback
```

The provider path consumes service-derived `ApprovedTrainingClaim[]`. It does not own bounded claim derivation.

## Authority order

The evidence layer does not replace exact anchors. The accepted authority order is:

```text
1. exact required training details
2. exact key_observation copy gate
3. required anchor count validation
4. approved bounded training claims
5. approved interpretation claims
6. approved coaching moves
```

The prompt must satisfy exact `key_observations` before using bounded claims, interpretation claims, or coaching moves.

## Runtime safety position

The provider remains strict. The backend rejects:

- paraphrased required anchors
- unsupported progression claims
- broad effort claims
- form/control claims
- recovery/fatigue claims outside approved context
- planned-work alignment claims without approved anchors
- single-session facts converted into broad trends
- wrapper objects
- extra keys
- raw/unbounded provider output

Provider output is used only after strict parser and validator approval. Invalid output falls back deterministically.

## Boundaries

This milestone does not wire the training section into full report assembly.

It does not change Streamlit, report persistence, workout generation, nutrition/recovery systems, or CrewAI behavior.

It does not make `direct_ollama` the default.

It does not persist raw provider output.

It does not expose raw provider output publicly.

## Runtime metadata

The service result exposes debug metadata separately from the approved public section, including provider/model selection, parse and validation status, fallback state, raw output diagnostics, matched anchors, and matched approved interpretation claims.

`required_anchor_count` is currently the minimum required threshold. It is possible for `matched_required_fact_anchors` to contain more entries than this threshold. That is not a failure when validation is approved, `missing_required_anchor_count` is zero, and validation errors are empty.

Optional future polish may rename this field to `required_minimum_anchor_count` and add `matched_anchor_count`, with no behavior change.

## Next recommended milestone

After Provider Promotion v1, run Expanded Training Evidence Runtime QA Matrix v1 before full report integration.

Suggested matrix areas:

- recovery_limited user
- nutrition_training_mismatch user
- data_quality_limited user
- incomplete actual-set logging
- plan-vs-actual substitutions
- missing/partial training evidence
- low-confidence training evidence

The purpose is not to make every model output pass. The purpose is to confirm the provider either validates cleanly or falls back safely while exact anchors remain mandatory.
