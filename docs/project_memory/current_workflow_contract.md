# Current Workflow Contract

This is the canonical developer workflow contract for the Health & Fitness Platform. If a supporting workflow document conflicts with this file, this file controls after explicit user authority, an approved Architecture handoff, `AGENTS.md`, and the project-memory source hierarchy.

## Authority boundaries

### User

The user owns product intent, priorities, milestone authorization, consequential external actions, final acceptance, and permission for destructive or externally visible operations.

### Architecture

Architecture owns milestone scope, technical direction, evidence requirements, review of the actual diff, acceptance determination, and Git closeout instructions. Architecture may correct a handoff after reconciling it with repository truth.

### Codex

Codex may inspect, implement the bounded milestone, run authorized validation, update required project memory, and report evidence. Codex does not independently expand scope, set product direction, self-accept work, or stage/commit/push/merge/snapshot without explicit authorization.

### Human UI/QA

Human QA owns final user-facing and browser acceptance when required. Automated checks and Codex browser evidence support that decision but do not replace it.

## Canonical environment

Windows is the canonical daily environment:

```text
C:\projects\fitness_ai
```

The primary runtime is:

```text
FastAPI       http://127.0.0.1:8000
Next.js prod  http://127.0.0.1:3100
Product URL   http://127.0.0.1:3100
```

Next.js development mode may run on port `3000` for iteration. It is optional and must not be substituted for production-build validation or required production browser smoke.

Linux remains available at `~/projects/fitness-ai-platform` as optional validation/runtime/demo infrastructure. Linux sync is optional and task-specific; it is not the canonical daily environment and does not require an automatic pull after every snapshot. Streamlit is legacy/developer-only.

## Phase flow

1. **Preflight and branch safety** — inspect the handoff, branch, exact base commit, recent history, full working-tree status, relevant diffs, current project memory, and affected contracts. Preserve all existing work and stop on a material mismatch.
2. **Implementation/apply** — make only authorized, narrow changes. Reuse existing ownership boundaries. Do not touch the real `fitness_ai.db` unless the milestone explicitly authorizes controlled data work.
3. **Targeted validation** — run the validation matrix slice appropriate to the change, then expand based on risk. Run lint/build for touched areas and project-memory checks when memory changes.
4. **Runtime/browser smoke when required** — UI-impacting work uses the production Next.js build on port `3100`, safe test data, console inspection, and a mobile-width check. Documentation/tooling-only work does not require browser smoke unless the handoff says otherwise.
5. **Explicit staging review** — inspect the exact diff, `git diff --check`, untracked files, staged files, database safety, and temporary artifacts. Never use `git add .`; stage only the reviewed file set after explicit authorization.
6. **Feature commit and push** — commit intentionally and push the feature branch only after staging authorization and validation.
7. **Architecture acceptance** — Architecture reviews the actual diff and evidence. Passing tests alone do not constitute acceptance.
8. **Merge and merged-main validation** — merge only after acceptance, perform the post-merge ancestry check proving the accepted feature commit is an ancestor of `main`, and rerun the required merged-main checks.
9. **Push main** — push validated `main` only after the required authority is explicit.
10. **External snapshot** — from clean validated `main`, create `C:\projects\fitness_ai_external\snapshots\fitness_ai_snapshot_YYYY-MM-DD_<commit>_main_<slug>.zip`.

Continue through safe mechanical steps inside an authorized phase. Stop and report on a wrong branch/base, unexpected worktree changes, validation failure, database risk, scope ambiguity, missing acceptance, or need for new external authority.

## Provider and product boundaries

Backend facts, calculations, constraints, validation, persistence, and fallback remain authoritative. Provider/AI output may propose or explain backend-approved options but must never silently control health decisions. AI-written daily prose is paused indefinitely. No provider, RAG, embedding, vector, runtime-agent, or health-recommendation scope is implied by this workflow.

## Repo-owned command layer

The canonical helpers live in `scripts/fitness_commands.ps1`; `local_developer_command_menu.md` defines their semantics. A PowerShell profile should only load the repo-owned script. The repository installer must back up existing profile content and may simplify the whole profile only through its explicit opt-in switch.
