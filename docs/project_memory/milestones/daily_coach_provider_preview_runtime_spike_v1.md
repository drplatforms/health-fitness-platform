# Daily Coach Provider Preview Runtime Spike v1

Status:

```text
DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_V1_IMPLEMENTATION_COMPLETE
```

Baseline:

```text
d5bfd29 Merge daily coach provider preview raw data payload v1
```

Branch:

```text
feature/daily-coach-provider-preview-runtime-spike-v1
```

Purpose:

Run the first developer-only provider-preview runtime spike from the raw Daily Coach provider-preview payload.

## Implemented

- Added `models/daily_coach_provider_preview_runtime_models.py`.
- Added `services/daily_coach_provider_preview_runtime_service.py`.
- Added `tools/dev_daily_coach_provider_preview_runtime_spike.py`.
- Added focused runtime service tests.
- Added focused developer tool tests.
- Updated project memory docs and project state.

## Runtime tool

```text
python tools/dev_daily_coach_provider_preview_runtime_spike.py --user-id 102 --target-date 2026-06-14 --model qwen2.5:3b
```

Optional flags:

```text
--timeout-seconds 300
--ollama-base-url http://localhost:11434
--temperature 0.9
--print-payload
```

## Provider input shape

The provider input is intentionally small:

```text
short role instruction
short authority boundaries
RAW_BACKEND_PAYLOAD_JSON:
<pretty JSON payload>
```

The raw backend payload remains the dominant input.

## Boundaries preserved

This milestone runs the first developer-only provider-preview runtime spike.

This milestone uses the raw provider-preview payload as the main input.

This milestone intentionally avoids backend-authored Daily Coach Note sentence templates.

This milestone does not use the old caged Daily Coach narrative prompt path.

This milestone does not parse, validate, score, reject, or approve provider output.

This milestone does not persist provider output.

This milestone does not change Today UI.

This milestone does not change Daily Coach Note public copy.

This milestone does not change Daily Next Action.

This milestone does not change API/schema/persistence/report/recommendation behavior.

This milestone does not promote any model.

This milestone lets the model roam in developer preview only.

Runtime result flags:

```text
developer_preview_only = true
provider_call_was_opt_in = true
persistence_allowed = false
product_surface_allowed = false
normal_today_surface_allowed = false
```

## What this deliberately avoids

```text
example Daily Coach Notes
good examples
bad examples
sentence skeletons
approved sentence templates
JSON output schema
exact keys required
copy this phrase exactly
say sentence one / sentence two / sentence three
coach_note/key_takeaway/recommended_focus schema
old Daily Coach narrative provider path
validation loop
correction loop
score/approval gate
normal Today surface integration
report integration
recommendation integration
persistence
```

## QA expectations

- Runtime spike is terminal-only and opt-in.
- Raw model output prints to terminal.
- Metadata prints separately from raw model output.
- Provider failures return error metadata and create no product effect.
- Tool writes no files by default.
- Already-built payload runtime path does not mutate the database.
- Tests do not call live Ollama.
