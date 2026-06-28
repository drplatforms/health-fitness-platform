# Next Milestone — Daily Coach Provider Prompt Lab / Voice Lab v1

Owner: Backend Development with Agent Engineering advisory and QA validation.

Baseline: `main` at `2835d09`.

Goal: build developer-only Prompt Lab / Voice Lab tooling so the team can compare Daily Coach prompt/context variants across fixed scenario days instead of continuing blind manual voice patches.

Required outputs:

- scenario registry;
- prompt/context variant registry;
- addressing policy diagnostics;
- food display language checks;
- sanitized selected outputs;
- comparison table;
- scoring template;
- validation summary;
- project memory contract.

Requested final status: `DAILY_COACH_PROVIDER_PROMPT_LAB_VOICE_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Next Milestone — Daily Coach Provider Plainspoken Voice & Action Clarity v5 QA

Owner: QA / Regression Testing with Backend and Agent Engineering support.

Baseline: implementation branch `feature/daily-coach-plainspoken-voice-action-clarity-v5`.

Recommended QA status: `DAILY_COACH_PROVIDER_PLAINSPOKEN_VOICE_ACTION_CLARITY_V5_QA_PASS`.

## Goal

Validate that v5 makes provider Daily Coach copy plainspoken, useful, and action-clear while preserving deterministic default, opt-in providers, strict parser behavior, approved-value quote validation, display permissions, and sanitized diagnostics.

## Primary cases

- user_id: 102 / date: 2026-06-05 / provider: openai / model: gpt-5.5
- user_id: 102 / date: 2026-06-27 / provider: openai / model: gpt-5.5
- user_id: 102 / date: 2026-06-03 / provider: openai / model: gpt-5.5
- user_id: 102 / date: 2026-06-06 / provider: openai / model: gpt-5.5

## Pass focus

- output says the actual action instead of packaging it as a slogan;
- rejected phrases such as `food move`, `clean work`, `make clean reps the win`, `the win is`, `protein bump`, `if it fits your meals`, and `Tuna, Canned in Water` do not appear in visible approved copy;
- friendly food labels are used when available;
- food action names the food, the macro reason, and the backed condition;
- training action is direct and natural;
- recovery implication explains what recovery means today without overclaiming;
- every concrete value/status/food/range remains declared in `quoted_values_used`;
- normal artifacts remain sanitized and raw provider output remains local-only diagnostics.

## Product-copy target

- plainspoken voice >= 4
- action clarity >= 4
- food specificity >= 4
- training clarity >= 4
- recovery implication >= 4
- grounding = 5
- product readiness >= 4
