# Daily Coach Provider Preview Raw Data Payload v1

Status target:

```text
DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_V1_IMPLEMENTATION_COMPLETE
```

Branch:

```text
feature/daily-coach-provider-preview-raw-data-payload-v1
```

Baseline:

```text
e26c4e0 Merge daily coach note copy QA matrix v1
```

Baseline snapshot:

```text
fitness_ai_snapshot_2026-07-01_e26c4e0_main_merge-daily-coach-note-copy-qa-matrix-v1.zip
```

## Purpose

Create a developer-only raw data payload for future provider preview.

This milestone builds the model's future data pasture: a wide, structured, source-labeled payload of deterministic backend facts, source services, completeness, gaps, confidence, limitations, and role boundaries.

## Implemented behavior

- Builds `DailyCoachProviderPreviewRawDataPayload` from a `DailyCoachIntelligenceSnapshot` object.
- Builds the same payload from a serialized snapshot dictionary.
- Provides a convenience builder for `user_id` and `target_date` through the existing Daily Coach Intelligence Snapshot service.
- Preserves raw source sections under `source_data`.
- Preserves `source_services`.
- Preserves `data_completeness`.
- Preserves `source_data_gaps`.
- Preserves `reason_codes`.
- Preserves `limitations`.
- Includes `backend_truth_contract`.
- Includes `provider_voice_space`.
- Includes `provider_input_guidance`.
- Includes `forbidden_provider_authority`.
- Serializes cleanly through `to_dict()`.
- Adds a developer terminal tool that prints JSON for inspection.

## Required boundary flags

```text
developer_preview_only = true
provider_call_allowed = false
persistence_allowed = false
product_surface_allowed = false
```

## Source data pasture

The payload preserves these source sections when available:

```text
recovery_intelligence
recovery_intelligence_v2
workout_set_intelligence
training_execution_summary
nutrition_trend_window
foundation_layer_status
data_completeness
source_data_gaps
reason_codes
limitations
```

The payload is intentionally structured data, not a final Daily Coach Note paragraph.

## Uncaged Provider Voice Principle

This milestone preserves the Uncaged Provider Voice Principle.

Future provider voice should be allowed to use natural coaching language and varied phrasing from backend facts.

Future provider work should not be forced into backend-authored sentence banks.

Future provider work should not be forced into repeated backend-authored sentence structures.

Future provider work should receive raw deterministic backend data, not only backend-written prose summaries.

Backend remains truth.

The model remains voice, explanation, synthesis, and candidate narrative only after Architecture explicitly authorizes provider behavior.

## Non-goals preserved

This milestone does not call providers.

This milestone does not generate Daily Coach Note copy.

This milestone does not change Today UI.

This milestone does not change API/schema/persistence/report/recommendation behavior.

This milestone does not change Daily Next Action selection.

This milestone does not add OpenAI/Ollama/CrewAI/RAG/agent behavior.

This milestone does not add model routing or Prompt Lab runtime behavior.

This milestone does not add workout plan behavior.

This milestone does not add nutrition target behavior.

This milestone does not add automatic deload or automatic progression behavior.

This milestone does not add wearable/HRV integration.

This milestone does not add medical interpretation.

## Forbidden payload shape

The payload must not become a hidden sentence bank and must not add top-level or `source_data` keys such as:

```text
approved_sentences
sentence_templates
final_coach_note
final_daily_coach_copy
rendered_note
safe_copy_options
```

## Validation focus

- Payload builds from object and serialized snapshot input.
- Raw source sections are preserved.
- Developer-only flags are enforced.
- Backend truth contract is included.
- Provider voice space rejects sentence-bank/pre-caged voice.
- Forbidden provider authority is explicit.
- Developer tool prints JSON to terminal.
- No provider modules are imported.
- Database is not mutated when wrapping an already-built snapshot.
