# Project Memory + Developer Workflow Canonicalization v1

Status: implementation in progress; not yet accepted.

Baseline:

```text
c8349e0 Merge public project rebrand and README refresh v1
```

Supporting accepted history:

```text
5f4ae50 Rebrand project as Health and Fitness Platform
c813f34 Merge strategic project memory sync before rebrand
11e8dad Synchronize strategic project memory before rebrand
```

## Problem

The public product surfaces now correctly identify the Health & Fitness Platform and the production Next.js application, but current developer-memory entry points and PowerShell helpers still describe the former AI-first, Linux/Streamlit-centered workflow. Fresh chats can therefore select the wrong runtime, source hierarchy, profile behavior, snapshot directory, and authority boundary.

## Authorized outcome

- Canonicalize current project-memory entry points around the Health & Fitness Platform identity.
- Make Windows at `C:\projects\fitness_ai` the canonical daily environment.
- Make FastAPI `8000` plus production Next.js `3100` the primary runtime and `http://127.0.0.1:3100` the product URL.
- Keep Next.js dev `3000` optional, Linux secondary, and Streamlit legacy/developer-only.
- Define one source hierarchy and explicit User/Architecture/Codex/human-QA authority boundaries.
- Align the repo-owned PowerShell command menu and safe profile installer with those contracts.
- Put snapshots in `C:\projects\fitness_ai_external\snapshots` and remove the old mandatory Linux-pull rule.
- Preserve deterministic/backend authority and the indefinite pause on AI-written daily prose.

## Canonical source hierarchy

1. Explicit current user authority.
2. Approved Architecture milestone/handoff reconciled with repository truth.
3. `AGENTS.md`.
4. `docs/project_memory/README.md`.
5. `docs/project_memory/current_state.md`.
6. `docs/project_memory/current_workflow_contract.md`.
7. Strategic architecture, led by `architecture/platform_north_star_and_future_stack.md`.
8. Active milestone, ADR, and affected design contracts.
9. Historical milestone/review/runtime-QA evidence.
10. Current validated code/runtime evidence when a supposedly current document is stale.

Validated repository evidence identifies drift but does not authorize Codex to expand Architecture scope.

## Authority boundaries

- The user owns product intent, priority, acceptance, final authority, and consequential external/destructive authorization.
- Architecture owns milestone selection/boundaries, technical direction, evidence requirements, actual-diff review, acceptance/rejection, and Git closeout flow.
- Codex owns bounded implementation, required tests, project-memory updates, and evidence reporting; it cannot self-accept or independently stage, commit, push, merge, snapshot, mutate the real profile, or change product direction.
- Human QA owns final browser/UI product acceptance where applicable.

## Helper and profile ownership

`scripts/fitness_commands.ps1` is the single repo-owned command source. The supported external PowerShell profile end state is a thin loader that only dot-sources this script. The installer preserves unknown profile content by default, backs up before writes, and exposes profile-wide simplification only through `-ReplaceProfileWithThinLoader`. Applying that switch to the real profile is deferred until post-review user action.

## Architecture correction requirements

Architecture review of the first unstaged implementation retained the canonical direction but required these safety corrections before acceptance:

- FastAPI commands target the repository's real `api.main:app` module.
- `fpull`/`gsync` synchronize clean canonical `main`; `fbranch` verifies `main == origin/main` before branch creation.
- `gacp` preserves explicit staging and refuses `main` unless the explicit `-AllowMain` escape hatch is deliberately authorized.
- `fmerge` requires the exact Architecture-accepted final commit and verifies that commit—not a movable branch tip—is an ancestor of merged `main`.
- `fsweep` remains the artifact-contamination scan; `gcheck` remains meaningful repository validation; `fmem` runs the full current memory-health workflow.
- Runtime starters refuse duplicate listeners. Stop helpers require listener/process-chain evidence tying the expected command to this repository and refuse unverified port owners.
- Top-level `project_state.json` pointers identify the current cleanup milestone and state that no application/backend milestone is authorized; historical nested milestone evidence remains intact.

Final Architecture continuation also required the developer assistant itself to stop foregrounding the historical provider/Linux/Streamlit era. Its generic outputs now use `main`/`origin/main`, the canonical source hierarchy, targeted risk-based validation, `frontend/` as the active Next.js surface, `ui/` as legacy tooling, Windows runtime helpers for FastAPI `8000` plus production Next.js `3100`, generic role/QA guidance, and a continuity brief centered on current identity, runtime, authority, and workflow. The next-milestone pointer now requires user roadmap input followed by fresh Architecture selection; it does not pre-authorize a product milestone.

## Non-goals

No application behavior, API, schema, persistence, provider feature, recommendation, workout, report, frontend UI, dependency, database, or runtime deployment change is authorized. This milestone must not initialize or mutate the real `fitness_ai.db`. It does not migrate a real user profile, start/stop product processes, run browser smoke, stage, commit, push, merge, or create a snapshot.

## Validation contract

- Focused command-menu/installer tests.
- Focused developer-assistant tests if that helper changes.
- Project-memory checker and its tests.
- Ruff check and format-check for touched Python files.
- PowerShell parser/load checks and installer execution only against a temporary profile.
- Non-destructive helper inspection smoke.
- Final Git diff/status/staged/artifact/database-safety audit.

Acceptance and Git closeout remain Architecture decisions after review of the actual unstaged diff and validation evidence.
