# Training Report Section Provider Boundary Hardening v1.1

## Status

Implemented / source-validated.

This milestone hardens the accepted Training Report Section Opt-In Provider Boundary v1 without changing provider behavior.

## Goal

Make the direct Ollama training report provider boundary cleaner before full report integration by:

- making runtime metadata self-contained
- moving provider-owned implementation into a formal service module
- preserving the existing spike script as a compatibility/runtime-QA wrapper
- keeping deterministic default and fallback behavior unchanged

## Provider Ownership

The formal provider implementation now lives in:

`services/training_report_section_direct_ollama_provider.py`

The existing runtime QA script remains at:

`scripts/spike_direct_ollama_training_report_section.py`

The script is now a thin compatibility CLI/import wrapper around the formal provider module. This preserves existing spike tests and runtime QA commands while moving provider ownership out of the script path.

## Public Service Boundary

The configured service boundary remains:

- `build_configured_training_report_section_with_metadata(...)`
- `build_configured_training_report_section(...)`

The public helper still returns only `ApprovedTrainingReportSection` content.

The metadata helper still returns the approved section plus runtime/debug metadata.

## Configuration Preserved

The same environment variables remain in use:

- `TRAINING_REPORT_SECTION_PROVIDER`
- `TRAINING_REPORT_SECTION_MODEL`
- `TRAINING_REPORT_SECTION_DIRECT_OLLAMA_TIMEOUT_SECONDS`

Default remains deterministic.

Opt-in remains `direct_ollama`.

The default opt-in model remains `ollama/qwen2.5:3b`.

## Runtime Metadata Hardening

`TrainingReportSectionRuntimeMetadata` now includes:

- `user_id`
- `report_date`

This makes debug artifacts self-contained without relying only on filenames or caller context.

Existing metadata is preserved, including:

- `configured_provider`
- `selected_provider`
- `configured_model`
- `selected_model`
- `provider_attempted`
- `fallback_used`
- `fallback_reason`
- `candidate_valid`
- `candidate_parse_status`
- `candidate_validation_status`
- `validation_status`
- `validation_errors`
- `final_section_source`
- `raw_output_length`
- `raw_output_preview_truncated`
- `markdown_wrapper_detected`
- `extra_keys_detected`
- `wrapper_object_detected`
- `elapsed_seconds`
- `provider_latency_ms`
- `required_anchor_count`
- `matched_required_fact_anchors`
- `missing_required_anchor_count`
- `matched_approved_interpretation_claims`
- `model_facing_quote_context`
- `approved_training_quote_context`

## Public Section Safety

`ApprovedTrainingReportSection` remains public-content only.

It does not include raw provider output, raw output previews, debug metadata, model-facing quote context, or approved quote context.

Raw/debug artifacts remain metadata/debug-side only.

## Behavior Preserved

This hardening pass does not change provider semantics.

Still preserved:

- deterministic provider remains default
- direct Ollama remains opt-in only
- qwen2.5:3b remains practical opt-in candidate
- qwen3 remains experimental only
- parser gating remains strict
- validator gating remains strict
- deterministic fallback remains required on invalid output
- no full AI Health Report integration is added
- no Streamlit/report persistence behavior is changed

## Testing Notes

Added/updated tests prove:

- deterministic default metadata includes `user_id` and `report_date`
- invalid-provider fallback metadata includes `user_id` and `report_date`
- approved direct Ollama metadata includes `user_id` and `report_date`
- fallback direct Ollama metadata includes `user_id` and `report_date`
- public approved section still excludes raw/debug fields
- provider service imports the formal direct Ollama provider module, not the script wrapper
- existing spike tests remain compatible through the script wrapper

## Runtime QA Required After Merge/Pull

After this hardening commit is pushed and pulled to Linux runtime, rerun the compact qwen2.5:3b formal boundary sweep across users 101-105.

Expected:

- user_id present in metadata
- report_date present in metadata
- provider_attempted correct
- fallback_used correct
- final_section_source correct
- raw/debug fields absent from public section
- no forbidden provider-facing terms
- no angle-bracket artifacts
- 5/5 approved or safe deterministic fallback with clear metadata

## Final Position

Provider Boundary Hardening v1.1 is a behavior-neutral architecture cleanup.

It prepares the training report section provider boundary for a future Architecture decision on Full Report Opt-In Integration v1.
