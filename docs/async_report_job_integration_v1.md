# Async / Report Job Integration v1

## Status

IMPLEMENTED / SOURCE VALIDATED

Branch: `feature/training-evidence-claim-service`

## Summary

Provider-backed full report generation is now protected by an async/background job boundary.

`direct_ollama` remains opt-in only. Even when the full-report training section provider gate is enabled, the provider is not attempted unless the report generation call is explicitly marked as an approved background/job context.

This prevents slow direct Ollama calls from accidentally running during normal synchronous report rendering or dashboard/page-load paths.

## Configuration

Existing config remains unchanged:

- `AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED`
- `TRAINING_REPORT_SECTION_PROVIDER`
- `TRAINING_REPORT_SECTION_MODEL`
- `TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS`

No additional environment variables were added.

## Behavior

### Default path

When `AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED` is unset or false:

- deterministic training section is used
- direct Ollama is not attempted
- full report generation remains fast/safe relative to provider path
- runtime metadata records `configured_provider=full_report_disabled`

### Enabled but unsafe synchronous context

When `AI_HEALTH_REPORT_TRAINING_SECTION_PROVIDER_ENABLED=true` but the caller has not explicitly marked the context as background/job-safe:

- direct Ollama is not attempted
- deterministic fallback training section is used
- runtime metadata records `fallback_reason=provider_requires_async_report_job`

### Approved async/background job context

The existing `/reports/generate/{user_id}` background job path now calls report generation with provider usage explicitly allowed.

When the full-report provider gate is enabled and `TRAINING_REPORT_SECTION_PROVIDER=direct_ollama`:

- the background report job may attempt the provider
- provider output still must parse and validate
- deterministic fallback is used if provider fails
- report job still completes when provider fails

## Report Job Status Metadata

`/reports/status/{job_id}` now includes safe training-section provider metadata under:

`training_section_provider`

The metadata may include:

- `report_job_id`
- `user_id`
- `report_date`
- `provider_enabled`
- `provider_attempted`
- `selected_provider`
- `selected_model`
- `fallback_used`
- `fallback_reason`
- `training_section_source`
- `provider_latency_ms`
- `validation_status`
- `validation_errors_count`

Raw provider output, prompt text, model-facing quote context, approved quote context payloads, and validator internals are not exposed in normal report job status.

## Public Content Safety

Rendered report content may include only approved/sanitized training section content:

- section summary
- key observations
- performance interpretation
- fatigue/recovery interpretation
- suggested focus
- limitations context
- deterministic fallback text

Rendered public report content must not include:

- raw output
- raw output preview
- model-facing quote context
- approved quote context payload
- parser debug fields
- validator internals
- validation error internals
- prompt text
- provider payloads

## Tests Added / Updated

Added:

- `tests/test_full_report_async_provider_integration.py`

Updated:

- `tests/test_training_report_section_full_report_integration.py`
- `tests/test_report_status.py`

Test coverage includes:

- deterministic default remains default
- provider disabled path does not call direct Ollama
- enabled provider is blocked outside async/job-safe context
- enabled provider can run inside async/job-safe context
- provider failure/fallback metadata remains safe
- report status includes safe provider metadata
- public rendered report content excludes raw/debug provider fields

## Validation

Focused validation passed:

```text
pytest tests/test_training_report_section_full_report_integration.py tests/test_full_report_async_provider_integration.py tests/test_report_status.py -q
12 passed

pytest tests/test_training_report_section_provider_service.py tests/test_direct_ollama_training_report_section_spike.py tests/test_training_evidence_claim_service.py tests/test_training_execution_summary_service.py tests/test_longitudinal_qa_seed_data.py tests/test_seed_training_execution_qa.py tests/test_report_status.py tests/test_api_smoke.py tests/test_training_report_section_full_report_integration.py tests/test_full_report_async_provider_integration.py -q
148 passed
```

Compile validation passed for touched and related files.

## Runtime QA Required

After commit/push/pull to Linux runtime, run compact async/background report job QA.

Expected:

- deterministic/default report generation does not call direct Ollama
- opt-in async report jobs may attempt direct Ollama
- provider metadata appears in job status
- report job completes successfully
- public report content has no raw/debug provider leakage
- users 101-105 either approve with qwen2.5:3b or fall back safely

## Final Position

Async / Report Job Integration v1 protects provider-backed full report generation from accidental synchronous use.

Direct Ollama remains opt-in only.

Deterministic remains default and fallback.

qwen2.5:3b remains the supported practical opt-in model.

qwen3 remains experimental only.
