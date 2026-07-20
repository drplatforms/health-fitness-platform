# Project Memory — Health & Fitness Platform

Project memory is the repository-owned continuity layer for the Health & Fitness Platform. It separates current operational truth, stable strategy, technical direction, workflow contracts, and historical evidence so that stale prose cannot compete with implementation authority.

## Canonical Source Hierarchy

When sources disagree, reconcile them in this order:

1. Explicit user authority and decisions.
2. The approved Architecture milestone or handoff, reconciled with repository truth.
3. `AGENTS.md`.
4. `docs/project_memory/current_truth.json` for operational current truth and implementation authorization.
5. `docs/project_memory/current_workflow_contract.md` for delivery and authority workflow.
6. `docs/project_memory/product_north_star.md` for stable product direction.
7. `docs/project_memory/product_roadmap.md` for comprehensive strategic capabilities and disposition.
8. The active milestone, affected architecture contracts, and ADRs.
9. Current validated code and runtime evidence.
10. Historical chronology, milestone records, reviews, runtime QA, and preserved source documents.

Code evidence can reveal stale documentation; it does not independently authorize new scope, a product-direction change, or acceptance.

## Minimal Default Grounding

Read only what the task needs.

For routine implementation or verification, begin with:

1. `current_truth.json`;
2. `current_workflow_contract.md`;
3. the active milestone or handoff;
4. directly affected contracts and the relevant validation matrix section.

Add strategic context only when the task needs it:

- `product_north_star.md` for the protected destination and product doctrine;
- `product_roadmap.md` for capability coverage, long-term sequencing, or strategic disposition.

Do not require the full roadmap for routine implementation when strategic context is irrelevant.

For future architecture or stack decisions only, add:

- `architecture/platform_north_star_and_future_stack.md`.

That technical reference is non-authorizing and is not a default strategic source.

## Information Classes

- **Current operational truth:** `current_truth.json`, with generated human-readable view `current_truth.md`.
- **Product North Star:** `product_north_star.md`.
- **Strategic Product Roadmap:** `product_roadmap.md`.
- **Future technical architecture:** `architecture/platform_north_star_and_future_stack.md` when specifically relevant.
- **Workflow authority:** `current_workflow_contract.md` plus scoped supporting delivery contracts.
- **History and evidence:** `current_state.md`, `next_milestone.md`, `project_state.json`, milestone/review/runtime-QA records, and `historical_strategy/`.

Compatibility paths such as `product_vision.md`, `premium_platform_blueprint.md`, and `future_architecture_ledger.md` are pointers only. They are not default reads or current strategic authorities.

## Delivery Workflow

`current_workflow_contract.md` is the canonical workflow contract. Supporting implementation detail lives in:

- `developer_delivery_workflow_contract.md`;
- `developer_delivery_workflow_script_safety_addendum_v1.md`;
- `development_workflow.md`;
- `local_developer_command_menu.md`.

Codex must not stage, commit, push, merge, snapshot, mutate the real database, or modify a real user profile unless the user explicitly authorizes that action. Architecture acceptance and Git closeout remain separate from implementation evidence.

## History and Memory Updates

Preserve historical milestone and review documents as evidence. Correct current-facing entry points instead of rewriting accepted chronology. Use historical files only when historical evidence is actually needed.

Meaningful behavior, architecture, workflow, or accepted-status changes require a same-branch project-memory update and project-memory validation.
