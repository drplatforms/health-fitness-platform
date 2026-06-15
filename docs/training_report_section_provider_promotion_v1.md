# Training Report Section Provider Promotion v1

## Status

Provider-boundary promotion after Training Evidence Claim Runtime QA v1.

## Decision

The service-backed direct-Ollama training report section path may remain available as an opt-in provider behind `TRAINING_REPORT_SECTION_PROVIDER=direct_ollama`.

Deterministic remains the default.

## Runtime validation baseline

Known-good scenario validated by Architecture:

- user_id: 102
- date: 2026-06-06
- model: `ollama/qwen2.5:3b`
- run count: 2
- validation_status: approved
- fallback_used: false
- candidate_parse_status: success
- candidate_validation_status: success
- validation_errors: []

## Accepted provider flow

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

## Safety boundaries

The provider path must continue rejecting:

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

## Non-goals

This milestone does not:

- wire into the full AI Health Report
- make `direct_ollama` default
- make qwen3 supported/default
- loosen parser behavior
- loosen validator behavior
- persist raw provider output
- expose raw provider output
- change Streamlit
- change workout generation
- change nutrition/recovery/report systems

## Follow-up

Run Expanded Training Evidence Runtime QA Matrix v1 before any full report integration.
