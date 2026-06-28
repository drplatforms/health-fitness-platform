# Daily Coach Prompt Lab / Voice Lab Contract v1

Status: Backend implementation milestone contract.

## Purpose

Daily Coach Prompt Lab / Voice Lab v1 is developer-only tooling for comparing Daily Coach provider prompt/context variants against fixed backend-approved scenario cases.

The lab exists because a provider candidate can be parser-valid, quote/value-valid, fallback-free, and still fail product voice. The lab evaluates both safety/grounding and product usefulness before another provider voice contract is selected.

## Boundaries

The lab must not:

- change normal Today behavior;
- promote OpenAI or any live provider;
- change deterministic default behavior;
- relax parser, quote/value validation, display permission checks, or fallback behavior;
- persist provider output into product data;
- expose raw provider output in default artifacts;
- write secrets, API keys, raw database rows, or chain-of-thought/scratchpad;
- create meal plans, food pairings, timing, serving units, or facts that Backend did not approve.

Live providers are explicit-only. OpenAI or direct_ollama lab runs must be skipped unless the developer passes the live-provider flag and has the needed environment configuration.

## Developer-only flow

Scenario registry → prompt/context variant registry → provider path → parser → validator → sanitized output capture → diagnostics → manual scoring template → comparison artifacts.

## Scenario registry

The v1 registry includes:

- `rich_nutrition_training_recovery` — user 102 / 2026-06-05
- `stable_comparison` — user 102 / 2026-06-27
- `training_present_nutrition_missing` — user 102 / 2026-06-03
- `nutrition_present_training_missing` — user 102 / 2026-06-06
- `data_quality_limited` — user 105 / 2026-06-27
- `recovery_limited` — user 101 / 2026-06-27

Default addressing policy forbids visible personal-name usage unless explicitly approved by scenario configuration.

## Prompt/context variants

The v1 registry includes:

- `current_v5_baseline`
- `minimal_examples`
- `plainspoken_fewer_bans`
- `food_action_focused`
- `first_person_logging_guidance`
- `higher_variation_same_validator`
- `friendly_food_labels_only`
- `canonical_vs_user_facing_food_separation`

Each variant includes a hypothesis, prompt/context changes, and safety boundaries.

## Food display language

The lab includes a small display-language layer only. It is not a nutrition catalog redesign.

Initial mappings:

- `Oats, Dry` → `oatmeal`
- `Tuna, Canned in Water` → `canned tuna`
- `White Rice, Cooked` → `rice`
- `Chicken Breast, Cooked, Skinless` → `chicken breast`
- `Greek Yogurt, Plain` → `Greek yogurt`

Canonical labels remain traceability labels. Friendly labels are preferred in visible copy. Blocked canonical labels are diagnostic failures when they leak into visible output.

## Artifacts

Default artifacts are sanitized and developer-only:

- `prompt_variant_summary.md`
- `scenario_matrix_summary.md`
- `selected_outputs_by_variant.md`
- `scoring_template.md`
- `comparison_table.csv`
- `comparison_table.md`
- `validation_summary.md`
- `run_config.json`

Default artifacts must not include raw provider output, secrets, API keys, environment dumps, raw database rows, or private notes.

## Manual scoring

QA scores each output 1-5 for:

- plainspoken voice
- action clarity
- scenario specificity
- food naturalness
- training clarity
- recovery clarity
- phrase variety
- logic coherence
- grounding
- product readiness

Grounding must be 5 for product acceptance.
