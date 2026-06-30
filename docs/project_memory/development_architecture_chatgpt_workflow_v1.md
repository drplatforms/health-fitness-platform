# Development Architecture — ChatGPT Project Workflow v1

**Status:** Active development-workflow architecture
**Current accepted main:** `123d115 main_merge-daily-coach-workout-set-intelligence-v1`

This ChatGPT Project is a seven-team development workspace, not a single chat with perfect memory.

## Core Rule

Repo docs are canonical. Chat context is useful, but it is not the source of truth. When a chat disagrees with repo docs, Architecture must re-study current repo docs, latest handoff, and accepted snapshot before issuing scope.

## Seven Team Workspace

The visible team/chat lanes are Architecture, Backend Development, QA, Agent Engineering, Streamlit UI / UX, Portfolio Packaging, and DevOps & Tooling.

Project Memory is not a visible team lane. It is a repo continuity responsibility shared by every lane.

## Snapshot + Handoff Discipline

Before a milestone, Architecture identifies accepted baseline commit and snapshot; Backend starts from that baseline; QA validates scoped branch/artifacts; final handoff records branch, commit, files, validation, known drift, and docs updates.

Do not assume an older chat has the latest state.

## Custom GPT Boundary

A custom GPT is not authorized yet. Custom GPT evaluation can happen later only after repo docs are clean and stable, team routing is canonical, current-state docs are reliable, and project memory is not stale.

## Prompt Lab Boundary

Prompt Lab is an engineering workflow, not a production runtime feature. It supports controlled prompt experiments, provider/model comparisons, cost tracking, rollback, and artifact safety. It does not authorize endless same-lane provider tuning when source data/backend intelligence is the bottleneck.

## Current State

Workout Set Intelligence v1 was merged at `123d115`. Provider voice iteration is paused. Active work is docs-only north-star canonicalization. After this milestone is accepted and snapshotted, archive the current Architecture chat and onboard a new Architecture chat from the latest snapshot, project memory, and the north-star file.


## Platform North Star Reference

The canonical long-term platform vision and future technology stack lives in:

```text
docs/project_memory/architecture/platform_north_star_and_future_stack.md
```

Read it before making future-stack, SaaS, RAG, vector, agent, model-routing, or product-platform decisions.
