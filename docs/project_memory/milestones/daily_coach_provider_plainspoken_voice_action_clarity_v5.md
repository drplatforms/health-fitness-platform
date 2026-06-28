# Daily Coach Provider Plainspoken Voice & Action Clarity v5

Status: Backend implementation in progress
Branch: feature/daily-coach-plainspoken-voice-action-clarity-v5
Baseline: 0ace3da Add daily coach provider human voice food action specificity v4

## Goal

Improve Daily Coach provider output so it sounds plainspoken, specific, and useful while preserving strict backend-owned truth, parser validation, quote/value validation, and deterministic fallback.

v5 is the final manual voice-correction milestone before the project should move to Prompt Lab / Voice Lab tooling if product voice still fails QA.

## Product target

The Daily Coach should answer:

1. Can I train today?
2. How should I train?
3. What nutrition issue matters?
4. What exact food action should I take, if any?
5. What should I avoid overdoing?

The output should not try to sound inspirational.
It should be useful.

Core rule:

> Say the actual action. Do not package it as a slogan.

## Implemented scope

v5 implements:

- plainspoken voice contract
- rejected phrase registry
- friendly food and food action context
- nutrition gap wording rules
- training and recovery wording rules
- prompt rewrite with plain examples
- validator and diagnostics updates
- trial matrix and QA scoring updates

## Safety boundaries

No factual authority moved to the provider.

Backend remains responsible for:

- facts
- targets
- actuals
- gaps
- statuses
- food suggestions
- display permissions
- validation
- fallback
- final approval

Provider may only:

- synthesize backend-approved facts
- write natural user-facing copy
- choose wording from approved meaning
- reference approved food options
- produce quote/value-declared JSON

## Explicit non-goals

v5 does not implement:

- OpenAI as default
- provider promotion
- deterministic default change
- parser relaxation
- quote/value validation relaxation
- deterministic fallback bypass
- raw database access for provider
- RAG
- embeddings
- multi-agent orchestration
- Prompt Lab
- Streamlit provider controls
- provider output persistence
- committed raw diagnostics
- meal planning changes
- workout generation changes
- nutrition target changes
- recovery score changes
- report composition changes
- normal Today page provider calls

## QA focus

Primary QA should evaluate:

- plainspoken voice
- action clarity
- food specificity
- training clarity
- recovery implication
- grounding
- product readiness

Primary acceptance target:

- plainspoken voice >= 4
- action clarity >= 4
- food specificity >= 4
- training clarity >= 4
- recovery implication >= 4
- grounding = 5
- product readiness >= 4

## Required provider behavior

Provider output should avoid rejected phrases such as:

- food move
- clean work
- make clean reps the win
- the win is
- useful move
- main lever
- support the work
- support the day
- nutrition support
- effort anchor
- planned effort range
- bigger nutrition overhaul
- rebuilding the whole plan
- if it fits your meals
- if it fits your day
- protein bump
- easy protein bump
- fatigue does not require backing off today
- Tuna, Canned in Water when a friendly label exists

Provider output should prefer direct phrasing such as:

- You can train as planned today.
- Keep a couple reps in reserve.
- Stop before the set turns into a grind.
- Calories and protein are both below target.
- Add canned tuna if you still need more protein.
- You do not need to overhaul the whole day.

## Validation expectation

Targeted validation should include:

- pytest tests/test_daily_coach_value_narrative_service.py -q
- pytest tests/test_daily_coach_narrative_validation_service.py -q
- pytest tests/test_daily_coach_provider_trial_matrix.py -q
- pytest tests/test_daily_coach_value_narrative_api.py -q
- pytest tests/test_daily_coach_synthesis_service.py -q
- pytest tests/test_api_smoke.py -q
- pytest tests/test_project_memory_check.py -q
- python tools/project_memory_check.py
- git diff --check
- targeted py_compile for touched model/service/tool/test files
