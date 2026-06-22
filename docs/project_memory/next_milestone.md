# Next Milestone

Last updated: 2026-06-22

## Latest accepted milestone

Daily Coach Async Provider Runtime Design v1

## Latest accepted status

`DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED`

## Current source branch

`main`

Latest accepted main merge snapshot:

`fitness_ai_snapshot_2026-06-22_0d3ab6a_merge-feature-daily-coach-async-provider-runtime-design-v1.zip`

## Current authorized milestone

Project Continuity System v2

Status:

`AUTHORIZED_FOR_BACKEND_DEVOPS_TOOLING_IMPLEMENTATION`

Required starting branch:

`feature/project-continuity-system-v2`

Milestone type:

Docs + tooling / project continuity

Expected recipient:

Backend Development / DevOps & Tooling

Expected validation type:

Docs-only validation plus targeted Python tooling checks.

## Recommended next milestone after Project Continuity System v2

Daily Coach Async Persistence Design v1

## Why this is next

The accepted Daily Coach Async Provider Runtime Design v1 raised the correct sequencing question: provider runtime should not proceed until durable async job/narrative storage boundaries are designed.

Persistence design should define what is durable, what remains Developer Mode-only, what metadata is safe, and why raw/rejected provider output should not be persisted.

## Not authorized yet

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3 promotion
- qwen3:32b promotion
- worker / queue / scheduler
- DB persistence implementation
- normal Today provider call
- public async narrative display
