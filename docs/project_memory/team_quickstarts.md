# Team Quickstarts

All roles start with the Health & Fitness Platform project-memory hierarchy: user authority, approved Architecture handoff reconciled with repo truth, `AGENTS.md`, project-memory `README.md`, `current_state.md`, and `current_workflow_contract.md`.

## Architecture

Read the active milestone and affected contracts, inspect repository truth, confirm scope/non-goals/evidence, and review the actual final diff before accepting. Architecture owns acceptance and closeout direction, not unapproved product intent.

## Backend/data

Treat backend facts, validation, constraints, persistence, calculations, and deterministic fallback as authoritative. Use isolated test databases and never initialize/mutate the real `fitness_ai.db` during automated validation.

## Frontend

The primary UI is Next.js. Validate lint and production build, then use production port `3100` for required browser smoke. Port `3000` is optional development mode. Streamlit is legacy/developer-only.

## DevOps/tooling

Windows at `C:\projects\fitness_ai` is canonical. Keep command logic in `scripts/fitness_commands.ps1`; profiles only load it. Snapshots go to `C:\projects\fitness_ai_external\snapshots`. Linux is secondary and optional.

## Codex

Implement only the authorized milestone, preserve working-tree truth, validate proportionally, update memory, and stop with an unstaged evidence handoff unless further Git authority is explicit. Do not self-accept.

## Human QA

Own final user-facing acceptance and report exact visible behavior, viewport coverage, console failures, and data side effects.
