# Backend Handoff Current

Updated: 2026-06-21

## Current State

Daily Coach Async Contracts + Data Model v1 has been accepted.

Backend now has foundational contracts for future async Daily Coach narrative job handling.

Accepted files include:

- models/async_daily_coach_narrative_models.py
- services/async_daily_coach_context_identity.py
- tests/test_async_daily_coach_narrative_contracts_v1.py

## Important Runtime Boundary

The canonical app runtime is Linux.

- `app` launches Linux FastAPI + Streamlit through SSH/tmux.
- `wapp` is Windows-local only.
- Windows hosts Ollama.
- Linux runtime uses Windows Ollama through LAN URL.

## Current Async Boundary

Not authorized yet:

- provider runtime execution
- background worker
- queue
- scheduler
- DB schema change
- daily_coach_narrative_jobs table
- provider cache
- normal Today provider call
- UI async display
- model promotion
- qwen3 bridge eligibility

## Recommended Next Backend Milestone

Daily Coach Async Service Shell / No Worker v1

Expected scope:

- create/read/latest service behavior
- stale/context-valid behavior
- in-memory or repository-shell behavior only if Architecture authorizes it
- tests proving no provider execution and no normal Today provider call

Still excluded:

- provider runtime
- worker
- queue
- scheduler
- normal UI display
