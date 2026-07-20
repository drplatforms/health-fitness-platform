# Project Memory — Health & Fitness Platform

Project memory is the repository-owned continuity layer for the Health & Fitness Platform. It records accepted product truth, architecture boundaries, delivery rules, current status, and historical evidence. Chat memory and a local PowerShell profile are not authoritative substitutes.

## Canonical source hierarchy

When sources disagree, reconcile them in this order:

1. Explicit user authority and decisions.
2. The approved Architecture milestone or handoff, reconciled with repository truth.
3. `AGENTS.md`.
4. This entry point.
5. `current_truth.json` for operational current truth and implementation authorization.
6. `current_workflow_contract.md`.
7. Strategic architecture and product-boundary documents, including `product_roadmap.md`.
8. The active milestone, ADRs, and affected contracts.
9. Historical chronology in `current_state.md`, `next_milestone.md`, and `project_state.json`.
10. Historical milestone, review, and runtime-QA evidence.
11. Current validated code/runtime evidence when a document is stale.

Code evidence can reveal stale documentation; it does not independently authorize new scope, a product-direction change, or acceptance.

## Required starting files

Read the smallest relevant set, beginning with:

1. `current_truth.json`
2. `current_workflow_contract.md`
3. `product_roadmap.md` for strategic direction only
4. `product_vision.md`
5. `architecture_principles.md`
6. `backend_truth_contract.md`
7. `ai_boundaries.md`
8. the active milestone and affected architecture contracts
9. `validation_matrix.md`

Use `team_routing_contract.md`, `team_quickstarts.md`, and the applicable role bootstrap when preparing a specialist handoff.

## Current product and runtime truth

- Product name: **Health & Fitness Platform**.
- Public repository identity: `health-fitness-platform`.
- Canonical daily development/runtime environment: Windows at `C:\projects\fitness_ai`.
- Primary product runtime: FastAPI on port `8000` plus the production Next.js frontend on port `3100`.
- Canonical product URL: `http://127.0.0.1:3100`.
- Next.js development mode on port `3000` is optional and is not acceptance evidence by itself.
- Linux at `~/projects/fitness-ai-platform` is secondary, optional validation/runtime/demo infrastructure.
- Streamlit is legacy/developer-only and is not part of the canonical product runtime.
- Provider/AI output is non-authoritative. AI-written daily prose is paused indefinitely.

## Delivery workflow

`current_workflow_contract.md` is the canonical workflow contract. Supporting implementation detail lives in:

- `developer_delivery_workflow_contract.md`
- `developer_delivery_workflow_script_safety_addendum_v1.md`
- `development_workflow.md`
- `local_developer_command_menu.md`

The normal phase flow is preflight and branch safety, bounded implementation, targeted validation, runtime/browser smoke only when required, explicit staging review, feature commit/push, Architecture acceptance, merge, merged-main validation, main push, and external snapshot. Stop at meaningful failures or risks rather than between every mechanical command.

Codex must not stage, commit, push, merge, snapshot, mutate the real database, or modify a real user profile unless the user explicitly authorizes that action. Architecture acceptance and Git closeout remain separate from implementation evidence.

Snapshots belong in `C:\projects\fitness_ai_external\snapshots` and are created only from clean, validated `main`. A Linux pull is optional and task-specific, not an automatic post-snapshot requirement.

## History and memory updates

Preserve historical milestone and review documents as evidence. Correct current-facing entry points instead of rewriting history. Meaningful behavior, architecture, workflow, or accepted-status changes require a same-branch project-memory update and project-memory validation.
