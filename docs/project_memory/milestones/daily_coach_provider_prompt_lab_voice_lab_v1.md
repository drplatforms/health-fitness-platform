# Milestone — Daily Coach Provider Prompt Lab / Voice Lab v1

Status: Backend implementation in progress.

Requested Backend status: `DAILY_COACH_PROVIDER_PROMPT_LAB_VOICE_LAB_V1_IMPLEMENTATION_COMPLETE`.

Baseline: `main` at `2835d09 Merge daily coach plainspoken voice action clarity v5`.

Baseline snapshot: `fitness_ai_snapshot_2026-06-28_2835d09_main_merge-daily-coach-plainspoken-voice-action-clarity-v5.zip`.

## Goal

Build developer-only Prompt Lab / Voice Lab tooling for Daily Coach provider prompt/context evaluation.

This milestone stops the blind v6 phrase-patch loop. It gives Architecture, QA, Backend, and Agent Engineering a repeatable way to compare prompt/context variants across fixed scenario days with the same parser, validator, fallback boundary, and manual scoring rubric.

## Implemented shape

Backend adds:

- typed lab contracts in `models/daily_coach_prompt_lab_models.py`;
- orchestration and artifact generation in `services/daily_coach_prompt_lab_service.py`;
- PowerShell-friendly CLI in `tools/dev_daily_coach_prompt_lab.py`;
- required scenario registry;
- required prompt/context variant registry;
- addressing policy diagnostics;
- small food display-language layer;
- sanitized artifact generation;
- manual scoring template;
- tests for service, diagnostics, artifacts, and CLI behavior.

## Non-goals

Do not implement:

- OpenAI as default;
- provider promotion;
- deterministic default changes;
- parser relaxation;
- quote/value validation relaxation;
- product persistence of provider output;
- public Streamlit Prompt Lab UI;
- normal Today provider calls;
- RAG, embeddings, multi-agent orchestration, worker, queue, scheduler, or background process;
- giant food catalog import;
- meal planning or food pairing generation.

## Acceptance focus

QA should pass v1 if:

- required scenarios are present;
- required variants are present;
- default addressing policy blocks hardcoded `Dustin` usage;
- food display mappings exist for current problematic labels;
- artifacts are generated and sanitized by default;
- live provider runs require explicit opt-in;
- existing provider trial matrix and deterministic Daily Narrative Voice Lab remain stable;
- normal Today behavior is unchanged;
- project memory docs are updated.
