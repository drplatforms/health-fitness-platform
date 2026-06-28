# Daily Coach Narrative Provider Trial Matrix v1

This directory is the recommended output location for Daily Coach Narrative Provider Trial Matrix v1.

The trial matrix compares the accepted Daily Coach value-aware narrative path across:

- deterministic;
- direct_ollama;
- openai.

## Usage

Deterministic-only trial:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers deterministic \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1
```

Dry run with live providers skipped:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 101 102 103 104 105 \
  --date 2026-06-27 \
  --providers deterministic direct_ollama openai \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1
```

Live-provider trial requires explicit opt-in:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 101 102 103 104 105 \
  --date 2026-06-27 \
  --providers deterministic direct_ollama openai \
  --models direct_ollama=ollama/qwen2.5:3b openai=gpt-4.1-mini \
  --output-dir docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1 \
  --allow-live-providers
```


## Diagnostics v1 additions

Daily Coach Provider Trial Diagnostics v1 adds local-only diagnostics for provider-runtime investigation.

Diagnostic mode is explicit and off by default. Normal trial artifacts remain sanitized and must not contain raw provider text or secrets.

Local raw provider text capture:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers openai \
  --models openai=gpt-4.1-mini \
  --output-dir /tmp/daily_coach_trials \
  --allow-live-providers \
  --diagnostic-raw-output \
  --raw-output-dir /tmp/fitness_ai_provider_diagnostics
```

Ollama cleanup after live trial rows:

```bash
python tools/run_daily_coach_provider_trial_matrix.py \
  --users 102 \
  --date 2026-06-27 \
  --providers direct_ollama \
  --models direct_ollama=ollama/qwen2.5:3b \
  --output-dir /tmp/daily_coach_trials \
  --allow-live-providers \
  --ollama-unload-after-run \
  --ollama-keep-alive 0
```

Safe diagnostic metadata may include provider error type, safe provider config status, live-provider allowance, diagnostic-mode status, and Ollama cleanup status. API keys, authorization headers, and raw provider text must not be written to normal JSONL/Markdown artifacts.

## Generated files

The tool writes:

- `trial_matrix.jsonl`
- `trial_matrix_summary.md`
- `selected_outputs.md`

Generated outputs should not include raw provider output or secrets. Review generated files before committing any trial artifacts.

## Product boundary

This is evaluation tooling only.

No provider becomes default through this milestone.

Deterministic remains the product default.

## Copy Grounding & Context Enrichment v1 additions

Provider trial rows now include diagnostic review fields for context-specific copy quality:

- `high_value_claims_available`
- `high_value_claims_used`
- `preferred_claims_by_field_used`
- `declared_claim_count`
- `generic_copy_flags`
- `unsupported_claim_flags`
- `section_role_flags`
- manual copy quality, specificity, coaching usefulness, and fact-dump score placeholders

These fields are review aids for Architecture/Product/Agent Engineering. They do not weaken parser, quote/value validation, deterministic fallback, or artifact safety. Raw provider output remains local-only and explicit diagnostic mode only.

---

## V2 Context Selection & Coaching Synthesis Review Fields

Daily Coach Provider Context Selection & Coaching Synthesis v2 extends the trial matrix with diagnostics for before/after provider review.

New review fields may include:

- `today_story_day_type`
- `today_story_primary_claim_keys`
- `today_story_optional_action_claim_keys`
- `high_value_claims_available_count`
- `high_value_claims_used_count`
- `preferred_claims_used_by_field`
- `claim_budget_min`
- `claim_budget_max`
- `quoted_claim_count`
- `today_story_used`
- `food_suggestion_available`
- `food_suggestion_used`
- `field_budget_flags`
- `weak_priority_action_flag`
- `fact_dumping_flag`
- `synthesis_quality_notes`
- `manual_actionability_score`

These diagnostics are review aids. They do not replace parser validation, quote/value validation, or deterministic fallback.

Adaptive verbosity should be judged by usefulness and scannability, not word count alone. Longer copy is acceptable when it connects approved nutrition, training, and recovery context into a clearer priority action. Longer copy is not acceptable when it becomes generic, repetitive, report-like, or unsupported.
