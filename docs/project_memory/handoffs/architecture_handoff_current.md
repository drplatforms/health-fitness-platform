# Architecture Handoff Current

Updated: 2026-06-21

## Current Accepted Milestones

Recent accepted milestones:

- Local Developer Command Menu App Runtime Correction v1
- Async Daily Coach Narrative Implementation Plan v1
- Daily Coach Async Contracts + Data Model v1

## Current Architecture Decision

Daily Coach Async Contracts + Data Model v1 is accepted.

Accepted status:

DAILY_COACH_ASYNC_CONTRACTS_DATA_MODEL_V1_ACCEPTED

Accepted feature commit:

74a6bd5 Add daily coach async narrative contracts

## Runtime Boundary Reminder

The command-menu hotfix restored the accepted runtime split:

- Windows is the source-of-truth development/control machine.
- Windows hosts Ollama.
- Linux is the canonical FastAPI + Streamlit runtime.
- `app` launches Linux runtime.
- `wapp` is the explicit Windows-local launcher.

## Async Boundary Reminder

Daily Coach async contracts are foundational only.

Not implemented:

- async runtime
- provider execution
- worker
- queue
- scheduler
- DB schema
- provider cache
- normal Today provider call
- UI async display
- model promotion
- qwen3 bridge eligibility

## Recommended Next Milestone

Daily Coach Async Service Shell / No Worker v1

Owner:

Backend Development / Service Layer

Purpose:

Implement service-layer create/read/latest/stale behavior using the accepted contracts, without provider runtime execution and without normal Today UI behavior changes.
