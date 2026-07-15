# Codex Handoff Rules

Every Codex handoff must identify the Health & Fitness Platform repository, exact expected branch/base, authoritative working-tree assumptions, authorized scope/non-goals, database/runtime/browser boundaries, required validation, allowed Git endpoint, and expected final evidence.

Codex resolves context using this hierarchy: explicit user authority; approved Architecture handoff reconciled with repo truth; `AGENTS.md`; project-memory `README.md`; `current_state.md`; `current_workflow_contract.md`; strategic architecture; active milestone/contracts; historical evidence; then validated code/runtime evidence for stale documentation.

Codex may implement, test, update memory, and report within the bounded milestone. It may not expand scope, set product direction, self-accept, or stage/commit/push/merge/snapshot without explicit authority. It must preserve all pre-existing work and stop on material branch/base/scope conflicts, validation failure, database risk, or missing consequential authority.

For UI work, require production Next.js browser smoke on port `3100` unless explicitly waived. For docs/tooling-only work, do not invent browser smoke. Never use the real `fitness_ai.db` as automated test state.

The handoff closeout must report exact files, commands/results, skipped checks, browser coverage, database safety, artifacts, `git diff --check`, branch/status, and staged/committed state.
