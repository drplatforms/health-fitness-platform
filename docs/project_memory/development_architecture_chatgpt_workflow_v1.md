# Development, Architecture, and Codex Workflow v1

This supporting guide maps collaboration roles onto the canonical workflow in `current_workflow_contract.md`.

## User authority

The user sets product intent, priority, acceptance expectations, and authorization for consequential external or destructive actions. Ambiguous product direction returns to the user.

## Architecture authority

Architecture defines approved milestone scope and technical direction, reconciles handoffs with repository truth, specifies evidence, reviews the actual diff, determines acceptance, and directs Git closeout. Architecture decisions do not erase explicit user authority.

## Codex implementation role

Codex performs branch-safe inspection, bounded implementation, targeted testing, required project-memory updates, and an evidence-backed handoff. Codex must not expand product scope, silently change architecture, self-accept, or stage/commit/push/merge/snapshot without authorization.

## Specialist routing

Route by the affected ownership boundary, not by stale team labels:

- Backend/data for facts, persistence, APIs, deterministic calculation, and validation.
- Frontend for the production Next.js product surface.
- Architecture for cross-boundary contracts and acceptance.
- DevOps/tooling for repo-owned developer workflow and optional environment support.
- QA/human review for final visible behavior.

Streamlit is legacy/developer-only and does not define a canonical UI lane. Linux is secondary optional infrastructure. Provider/AI behavior remains non-authoritative, with AI-written daily prose paused indefinitely.

## Evidence flow

```text
authorized handoff
→ preflight and branch safety
→ narrow implementation
→ targeted validation
→ production browser smoke when UI-impacting
→ project-memory update
→ exact diff and evidence review
→ Architecture acceptance
→ explicitly authorized Git closeout
```
