# Architecture Milestone Closeout Command Template

$HeaderPattern = '(?s)\A# Historical Milestone Chronology\r?\n\r?\n> This file preserves historical milestone chronology\. It is not operational authority\. Current operational truth is owned by `docs/project_memory/current_truth\.json`\.\r?\n\r?\n'
$HeaderMatch = [regex]::Match($ExistingState, $HeaderPattern)

if (-not $HeaderMatch.Success) {
    throw "current_state.md is missing its historical chronology header."
}

This is the canonical executable closeout ceremony for `fitness_ai` Architecture chats.

Reuse these known-good commands for routine closeout. Architecture substitutes milestone-specific values; it does not reinvent equivalent Git or PowerShell flows. When a canonical phase cannot apply, Architecture must explain the technical reason before deviating.

The user runs the phases in order. Stop only when a command fails or output looks wrong. Otherwise continue through the canonical phases. Routine closeout requires only the final Phase 8 pasteback.

Architecture owns acceptance and Git closeout. Codex stops without staging, committing, pushing, merging, or snapshotting.

## Canonical lifecycle

1. Phase 1 — record acceptance state
2. Phase 2 — validate before staging
3. Phase 3 — exact-file staging
4. Phase 4A — feature commit
5. Phase 4B — feature push
6. Phase 4C — local `main` merge
7. Phase 5 — merged-main automated validation
8. Phase 6 — merged-main production smoke when required
9. Phase 7A — push `main`
10. Phase 7B — snapshot
11. Phase 8 — final pasteback

Keep commit, feature push, and local merge in separate phases. A failed commit must never flow into feature push or branch switching. A failed feature push must never flow into merge. Do not continue into the next phase after any failure or suspicious output.

## Phase 1 — record acceptance state

Routine milestone acceptance updates only:

- `docs/project_memory/current_state.md`
- `docs/project_memory/current_truth.json`
- generated `docs/project_memory/current_truth.md`

`project_state.json` is historical compatibility evidence and is not part of routine acceptance-state commands. Change `next_milestone.md` or `product_roadmap.md` only when its actual content changes. Never edit `current_truth.md` manually. Architecture replaces every applicable placeholder below.

```powershell
cd C:\projects\fitness_ai
$StatePath = "C:\projects\fitness_ai\docs\project_memory\current_state.md"
$ExistingState = Get-Content -LiteralPath $StatePath -Raw
$NewSection = @'
# Accepted Milestone - {{MILESTONE_NAME}}
Canonical implementation baseline before merge: main at {{BASELINE_COMMIT}}.
Feature branch: {{FEATURE_BRANCH}}.
Status: {{ACCEPTANCE_TOKEN}}
Accepted behavior:
- {{ACCEPTED_BEHAVIOR}}
Roadmap status:
{{MILESTONE_NAME}} is accepted. The immediate next priority remains {{NEXT_MILESTONE}} and is not implementation-authorized unless Architecture explicitly says otherwise.
---
'@
if ($ExistingState -notmatch [regex]::Escape("{{ACCEPTANCE_TOKEN}}")) {
    [System.IO.File]::WriteAllText(
        $StatePath,
        $ExistingState.Insert($HeaderMatch.Length, $NewSection + [Environment]::NewLine),
        [System.Text.UTF8Encoding]::new($false)
    )
}
$TruthPath = "C:\projects\fitness_ai\docs\project_memory\current_truth.json"
$Truth = Get-Content -LiteralPath $TruthPath -Raw | ConvertFrom-Json
$Truth.active_milestone.id = "none"
$Truth.active_milestone.name = "No active implementation milestone"
$Truth.active_milestone.status = "NO_IMPLEMENTATION_AUTHORIZED"
$Truth.implementation_authorization.status = "NOT_AUTHORIZED"
$Truth.implementation_authorization.authority = "Architecture"
$Truth.implementation_authorization.scope = "No implementation beyond the accepted milestone is authorized."
$Truth.immediate_next_priority.id = "{{NEXT_PRIORITY_ID}}"
$Truth.immediate_next_priority.name = "{{NEXT_MILESTONE}}"
$Truth.immediate_next_priority.status = "PENDING_ARCHITECTURE_SCOPING"
$Json = $Truth | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText(
    $TruthPath,
    $Json + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)
.\.venv\Scripts\python.exe tools\current_truth.py write --project-root .
.\.venv\Scripts\python.exe tools\current_truth.py check --project-root .
```

## Phase 2 — validate before staging

Run repository-required mutating formatters before Phase 3 so pre-commit hooks do not create a staged/unstaged split during commit.

```powershell
cd C:\projects\fitness_ai
{{MUTATING_FORMAT_COMMANDS_IF_REQUIRED}}
{{FORMAT_LINT_CHECKS}}
{{FEATURE_BRANCH_VALIDATION}}
.\.venv\Scripts\python.exe -m pytest `
  tests/test_project_memory_check.py `
  -q
.\.venv\Scripts\python.exe -B `
  tools\project_memory_check.py `
  --project-root .
git diff --check
git branch --show-current
git status --short --untracked-files=all
git diff --cached --name-only
```

Expected: the accepted feature branch, only reviewed milestone files, no staged files, and all required checks green.

## Phase 3 — exact-file staging

Never use `git add .` or `git add -A`.

```powershell
cd C:\projects\fitness_ai
git branch --show-current
git status --short --untracked-files=all
git add `
  {{FILE_1}} `
  {{FILE_2}} `
  {{FILE_3}} `
  docs/project_memory/current_state.md `
  docs/project_memory/current_truth.json `
  docs/project_memory/current_truth.md
if ($LASTEXITCODE -ne 0) { throw "Exact-file staging failed." }
git status --short --untracked-files=all
git diff --cached --name-status
git diff --cached --check
```

Confirm that only the accepted files are staged. For a rare rename or deletion under an ignored path, Architecture may supply a milestone-specific exact command when the normal block cannot apply.

## Phase 4A — feature commit

```powershell
cd C:\projects\fitness_ai
git commit -m "{{FEATURE_COMMIT_MESSAGE}}"
if ($LASTEXITCODE -ne 0) { throw "Feature commit failed." }
git status --short
git log --oneline -3
```

## Phase 4B — feature push

```powershell
cd C:\projects\fitness_ai
git push -u origin {{FEATURE_BRANCH}}
if ($LASTEXITCODE -ne 0) { throw "Feature push failed." }
```

## Phase 4C — local `main` merge

```powershell
cd C:\projects\fitness_ai
$AcceptedFeatureCommit = git rev-parse {{FEATURE_BRANCH}}
if ($LASTEXITCODE -ne 0) { throw "Feature commit resolution failed." }
git checkout main
if ($LASTEXITCODE -ne 0) { throw "Checkout of main failed." }
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw "Fast-forward pull of origin/main failed." }
git merge --no-ff `
  {{FEATURE_BRANCH}} `
  -m "{{MERGE_MESSAGE}}"
if ($LASTEXITCODE -ne 0) { throw "No-ff merge failed." }
git merge-base --is-ancestor $AcceptedFeatureCommit main
if ($LASTEXITCODE -ne 0) { throw "Accepted feature commit is not an ancestor of main." }
git status --short
git log --oneline -5
```

Do not push `main` yet.

## Phase 5 — merged-main automated validation

```powershell
cd C:\projects\fitness_ai
{{MERGED_MAIN_VALIDATION}}
.\.venv\Scripts\python.exe -B `
  tools\project_memory_check.py `
  --project-root .
git diff --check
git status --short
```

Use milestone-specific targeted checks. Add a canonical database before/after hash guard only when validation could access it, and never run automated validation against writable canonical data.

## Phase 6 — merged-main production smoke when required

For UI milestones, run production-mode smoke from merged local `main` with safe temporary data. `next dev` is not an acceptance surface.

```text
{{MERGED_MAIN_SMOKE_CHECKLIST}}
```

Do not push `main` until required smoke is green. For non-UI milestones, Architecture states why this phase does not apply.

## Phase 7A — push `main`

```powershell
cd C:\projects\fitness_ai
git push origin main
if ($LASTEXITCODE -ne 0) { throw "Final main push failed." }
```

## Phase 7B — snapshot

```powershell
cd C:\projects\fitness_ai
$Commit = git rev-parse --short HEAD
$Date = Get-Date -Format "yyyy-MM-dd"
$SnapshotPath = "C:\projects\fitness_ai_external\snapshots\fitness_ai_snapshot_${Date}_${Commit}_main_{{SNAPSHOT_SLUG}}.zip"
git archive `
  --format zip `
  --output $SnapshotPath `
  HEAD
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $SnapshotPath)) {
    throw "Snapshot creation failed."
}
Write-Host "Snapshot path: $SnapshotPath"
```

## Phase 8 — final pasteback

This is the only routine pasteback required.

```powershell
cd C:\projects\fitness_ai
Write-Host "Branch:"
git branch --show-current
Write-Host "Status:"
git status --short
Write-Host "Recent commits:"
git log --oneline -8
Write-Host "Local main:"
git rev-parse --short main
Write-Host "Origin main:"
git rev-parse --short origin/main
Write-Host "Snapshot path:"
Write-Host "{{SNAPSHOT_PATH_FROM_PHASE_7B}}"
```

Architecture confirms branch `main`, a clean working tree, local `main` equals `origin/main`, the accepted feature commit is in `main` ancestry, the `--no-ff` merge exists, and the snapshot came from exact merged-main HEAD. Architecture then closes the milestone.
