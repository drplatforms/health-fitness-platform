# Daily Coach Provider Trial Diagnostics v1

Status: Backend implementation patch prepared.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

## Summary

This milestone adds diagnostics to the Daily Coach provider trial matrix so provider failures can be understood without changing product runtime behavior.

## Scope implemented

- local-only raw provider output diagnostic mode, explicit and off by default;
- safe raw diagnostic files written outside normal JSONL/Markdown artifact flow;
- safe provider config metadata;
- OpenAI missing-key/auth/model/rate/timeout/connection/malformed/parse/quote error classification where metadata allows;
- optional Ollama unload cleanup after live direct_ollama trial rows;
- cleanup failures recorded as safe metadata, not provider-quality failures;
- `.gitignore` entries for local QA/diagnostic folders;
- tests for default sanitization, missing key classification, mocked error classification, raw diagnostic opt-in, and cleanup behavior.

## Preserved boundaries

Deterministic remains default. direct_ollama and openai remain opt-in. No normal endpoint behavior, Streamlit UI, persistence, schema, parser, validator, quote/value, nutrition, workout, recovery, or report behavior changes. No tests call live providers.
