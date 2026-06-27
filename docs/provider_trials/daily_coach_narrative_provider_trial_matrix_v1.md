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
