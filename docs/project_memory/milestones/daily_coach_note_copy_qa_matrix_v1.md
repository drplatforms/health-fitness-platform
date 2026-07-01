# Milestone — Daily Coach Note Copy QA Matrix v1

Requested status:

```text
DAILY_COACH_NOTE_COPY_QA_MATRIX_V1_IMPLEMENTATION_COMPLETE
```

Baseline:

```text
33ebf18 Merge daily coach note recovery-aware language v1
```

Source snapshot:

```text
fitness_ai_snapshot_2026-07-01_33ebf18_main_merge-daily-coach-note-recovery-aware-language-v1.zip
```

## Purpose

This milestone adds QA/test/documentation coverage for Daily Coach Note public copy after the first recovery-aware language integration.

This milestone cages evaluation, not model voice.

The goal is to protect the current deterministic Daily Coach Note / Today card path while preserving the future direction that provider voice should be richer than backend-authored sentence banks.

## Implemented coverage

Added focused copy matrix coverage in:

```text
tests/test_daily_coach_today_card_copy_matrix.py
```

The matrix covers all approved Daily Next Action classes:

- `complete_recovery_checkin`
- `keep_training_conservative`
- `log_food`
- `review_workout`
- `review_report_guidance`
- `review_nutrition_targets`

The matrix covers these recovery contract states:

- no recovery contract
- unavailable recovery context
- limited recovery context
- usable low recovery pressure
- usable moderate recovery pressure
- usable high recovery pressure

## Verified behavior

The matrix verifies:

- no-contract Daily Coach Note behavior remains backward compatible
- `RecoveryAwareCoachCopyContract` object input remains valid
- serialized recovery contract dictionary input remains valid
- limited or unavailable recovery context produces cautious public wording
- low, moderate, and high recovery pressure paths remain bounded
- public payload does not expose provider/debug/internal contract terminology
- public payload does not expose unsafe medical, injury, overtraining, automatic deload, automatic progression, or unsafe-to-train claims
- `coach_note` remains at or below 520 characters
- Daily Next Action fields are not changed by recovery copy
- Daily Coach Note copy remains deterministic under the current service path
- provider calls do not occur in the deterministic Today card matrix path

## Repeated-template risk

The test/doc matrix explicitly flags repeated-template risk as a future provider evaluation concern.

Current deterministic copy is intentionally bounded, but future provider work should not be judged only by whether it can reproduce backend-written sentence structures. Provider QA should evaluate whether output remains grounded, safe, specific, useful, and varied enough across repeated daily use.

Future provider evaluation should watch for:

- the same sentence skeleton appearing every day
- generic recovery-pressure phrasing that ignores available source facts
- sanitized paragraphs that already sound like the final answer before the model receives them
- provider output that is safe but too bland to be useful
- provider output that becomes more repetitive because the backend pre-caged the voice

## Uncaged Provider Voice Principle

Uncaged provider voice means:

- give the model rich deterministic source data
- include source facts, confidence, limitations, recovery/training/nutrition indicators, and user context
- do not reduce the input to a sanitized paragraph that already sounds like the final answer
- do not force the model to choose from approved sentence templates
- do not require repeated backend-authored sentence structures
- evaluate the output after generation instead of pre-caging the voice

Future provider voice should receive raw deterministic backend data, not only backend-written prose summaries.

## Backend authority preserved

Backend owns truth.

Backend owns facts.

Backend owns constraints.

Backend owns source data.

Backend owns confidence and provenance.

Backend owns persistence.

Backend owns final product authority.

Provider output is never truth.

Provider output does not mutate state.

Provider output does not change workouts, nutrition, recommendations, or Daily Next Action selection.

Provider output is developer/preview-only until Architecture separately authorizes product behavior.

## Explicit non-goals preserved

This milestone does not add or change:

- provider behavior
- OpenAI/Ollama/CrewAI behavior
- RAG/vector/agent behavior
- model routing
- Prompt Lab runtime
- Streamlit UI layout
- API routes
- database schema or migrations
- persistence behavior
- report behavior
- recommendation behavior
- Daily Next Action selection logic
- workout plan behavior
- nutrition target behavior
- automatic deload logic
- automatic progression logic
- wearable/HRV integration
- medical interpretation

## Validation focus

Focused validation should include:

```text
python -m pytest tests/test_daily_coach_today_card_copy_matrix.py -q
python -m pytest tests/test_daily_coach_today_card_service.py -q
python -m pytest tests/test_daily_coach_recovery_copy_contract_service.py -q
python -m pytest tests/test_daily_coach_intelligence_snapshot_service.py -q
python -m pytest tests/test_daily_coach_intelligence_snapshot_workout_set_v2.py -q
python -m pytest tests/test_recovery_intelligence_v2_seed_matrix.py -q
python -m pytest tests/test_recovery_intelligence_v2_service.py -q
python -m pytest tests/test_recovery_intelligence_v2_models.py -q
python -m pytest tests/test_recovery_intelligence_service.py -q
python -m pytest tests/test_project_memory_check.py -q
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
```

## Touched files

```text
tests/test_daily_coach_today_card_copy_matrix.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_note_copy_qa_matrix_v1.md
```
