# Direct Ollama Training Report Section Provider v1

## Status

Implemented as an opt-in provider extraction after `Direct Ollama Training Report Section Coach-Quality Copy v4.3`.

Provider v1 promotes the successful spike contract into a reusable service boundary while keeping deterministic output as the default.

## Provider configuration

Deterministic remains the default.

```text
TRAINING_REPORT_SECTION_PROVIDER=deterministic|direct_ollama
TRAINING_REPORT_SECTION_MODEL=ollama/qwen2.5:3b
TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS=60
```

`ollama/qwen2.5:3b` is the supported Provider v1 model. Other local models remain experimental and must pass the same parser, validator, and fallback contract before they are treated as supported.

## Architecture

Provider v1 preserves the spike architecture:

```text
backend-approved training quote context
→ quote-only model-facing payload
→ required fact anchors
→ anchor-first key observations
→ approved interpretation claims
→ approved coaching frames / style boundaries
→ structured JSON candidate
→ strict parser
→ strict validator
→ provider-approved output or deterministic fallback
```

## Boundaries

This milestone does not wire the training section into full report assembly.

It does not change Streamlit, report persistence, workout generation, or CrewAI behavior.

It does not make `direct_ollama` the default.

## Runtime metadata

The service result exposes debug metadata separately from the approved public section, including provider/model selection, parse and validation status, fallback state, raw output diagnostics, matched anchors, and matched approved interpretation claims.

The approved user-facing section does not expose provider/debug metadata.
