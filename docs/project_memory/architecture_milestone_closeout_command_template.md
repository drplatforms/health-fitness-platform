# Architecture Milestone Closeout Command Template

This is the canonical executable closeout ceremony for `fitness_ai` Architecture chats.

The bootstrap document defines authority. This document defines the exact operational sequence.

Reuse this approved known-good template for routine closeout. Any deviation must state the technical reason before the alternate commands are supplied.

Consequential PowerShell phases that depend on `throw`, `$LASTEXITCODE`, or other stop-on-failure guards must be issued as one executable script block, normally `& { ... }`. Do not assume a sequence of independently pasted top-level statements will stop executing after an earlier statement throws.

## 1. Mandatory Projectmem-first Codex orientation

When Projectmem MCP is available, every new Codex milestone must begin with:

1. `get_instructions`
2. `get_summary`
3. `get_project_map`

Use focused `get_context` only when a specific unresolved question justifies it. Then Codex should read the active handoff and the minimum directly relevant canonical project-memory, implementation, and test files.

Do not manually reread the broad `docs/project_memory` corpus by default.

If Projectmem is unavailable or fails, report that immediately and fall back to targeted canonical reads.

Every Codex completion report must include:

```text
Projectmem orientation report:
- MCP available: yes/no
- Projectmem tools used:
- Direct canonical project-memory files read:
- Broad repository scan performed: yes/no
```

## 2. Ownership

Architecture owns scope, handoffs, review, acceptance, acceptance-state project-memory updates, exact-file staging, commit, feature push, `--no-ff` merge, merged-main validation, merged-main smoke, final main push, snapshot, and final closeout verification.

Codex owns bounded implementation, implementation validation, authorized safe smoke, temporary-artifact cleanup, and completion reporting.

Codex must stop with nothing staged, committed, pushed, merged, or snapshotted.

## 3. Canonical closeout sequence

For normal UI/product milestones:

```text
Codex completion
→ trivial cleanup / status reconciliation
→ FEATURE-BRANCH USER PRODUCTION SMOKE
→ Architecture acceptance
→ RECORD ACCEPTANCE HISTORY AND CURRENT TRUTH
  current_state.md + current_truth.json + generated current_truth.md
→ validate project memory + diff-check
→ stage EXACT accepted files
→ verify staged set
→ commit feature
→ push feature branch
→ checkout main + pull
→ --no-ff merge
→ merged-main automated validation
→ MERGED-MAIN USER PRODUCTION SMOKE
→ push main
→ external git-archive snapshot
→ final pasteback
```

UI work has two distinct smoke gates:

1. feature-branch production smoke before Architecture acceptance;
2. merged-main production smoke after merge and before final `main` push.

Do not collapse them.

## 4. Do not invent routine extra gates

Do not routinely require giant diff pastebacks, external review patches, one-command-at-a-time supervision, repeated broad scans, or repeated full-suite runs.

Request targeted diff review only when a real risk exists: unexpected files, contradictory evidence, architecture-sensitive uncertainty, unexplained scope expansion, validation mismatch, or suspicious database/schema/API/provider/dependency changes.

Use medium-sized command phases and pause only at meaningful risk gates.

## 5. Phase A — cleanup and pre-smoke status

Architecture may directly remove obvious temporary artifacts.

```powershell
cd C:\projects\fitness_ai

Remove-Item `
  -LiteralPath "tmp\{{TEMP_FILE}}" `
  -Force `
  -ErrorAction SilentlyContinue

git branch --show-current
git rev-parse --short HEAD
git status --short --untracked-files=all
git diff --check
```

Expected: correct feature branch and baseline, only legitimate milestone files, nothing staged, and `git diff --check` green.

## 6. Phase B — feature-branch production smoke

For UI work use the normal acceptance surface:

```text
FastAPI: 127.0.0.1:8000
Next.js production: 127.0.0.1:3100
```

`next dev` is not an acceptance surface.

QA must not mutate `C:\projects\fitness_ai\fitness_ai.db`. Use safe temporary data.

Architecture gives a concise milestone-specific checklist. The user normally reports `green` or the specific failure.

## 7. Phase C — Architecture acceptance

After required validation and feature-branch smoke pass:

```text
Architecture acceptance: PASS — {{MILESTONE_NAME}}.
```

Only now is final canonical acceptance state recorded.

## 8. Phase D — update current_state.md

Always use an absolute path.

```powershell
cd C:\projects\fitness_ai

$StatePath = "C:\projects\fitness_ai\docs\project_memory\current_state.md"
$ExistingState = Get-Content -LiteralPath $StatePath -Raw
$HeaderPattern = '(?s)\A# Historical Milestone Chronology\r?\n\r?\n> This file preserves historical milestone chronology\. It is not operational authority\. Current operational truth is owned by `docs/project_memory/current_truth\.json`\.\r?\n\r?\n'
$HeaderMatch = [regex]::Match($ExistingState, $HeaderPattern)

if (-not $HeaderMatch.Success) {
    throw "current_state.md is missing its historical-ledger authority header."
}

$NewSection = @'
# Accepted Milestone - {{MILESTONE_NAME}}

Canonical implementation baseline: main at {{BASELINE_COMMIT}}.

Feature branch: {{FEATURE_BRANCH}}.

Status: {{ACCEPTANCE_TOKEN}}

Implementation scope:

- {{ACCEPTED_BEHAVIOR_1}}
- {{ACCEPTED_BEHAVIOR_2}}
- {{ACCEPTED_BEHAVIOR_3}}
- {{ACCEPTED_BEHAVIOR_4}}
- {{ACCEPTED_BEHAVIOR_5}}
- Required feature-branch validation and acceptance smoke passed.
- No unauthorized scope expansion was introduced.

Roadmap status:

{{MILESTONE_NAME}} is accepted.
The next recommended milestone is {{NEXT_MILESTONE}}.
The next milestone remains pending Architecture scoping and is not yet implementation-authorized.

---

'@

if ($ExistingState -notmatch [regex]::Escape("{{ACCEPTANCE_TOKEN}}")) {
    [System.IO.File]::WriteAllText(
        $StatePath,
        $ExistingState.Insert($HeaderMatch.Length, $NewSection),
        [System.Text.UTF8Encoding]::new($false)
    )
}
```

Architecture must replace all placeholders before giving this to the user.

## 9. Phase E — update current_truth.json and regenerate its view

The accepted milestone stays in the historical chronology. Unless Architecture has separately authorized a next implementation milestone, the kernel must fail closed to no active implementation authorization. Never store a Git hash, working branch, or clean/dirty state in the kernel; live Git owns those facts.

```powershell
cd C:\projects\fitness_ai

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

If Architecture has explicitly authorized the next milestone, replace the fail-closed values above with that exact authorization instead. Do not infer authorization from the roadmap or a planning ledger.

## 10. Phase F — validate acceptance state

Before staging:

```powershell
cd C:\projects\fitness_ai

git status --short --untracked-files=all
git diff --check

.\.venv\Scripts\python.exe -m pytest `
  tests/test_project_memory_check.py `
  -q

.\.venv\Scripts\python.exe `
  tools\project_memory_check.py `
  --project-root .
```

Architecture verifies the final exact working-tree file set.

## 11. Phase G — exact-file staging

Never use `git add .` or `git add -A`.

```powershell
cd C:\projects\fitness_ai

git branch --show-current
git status --short --untracked-files=all

$AddPaths = @(
    "{{FILE_1}}"
    "{{FILE_2}}"
    "{{FILE_3}}"
    "docs/project_memory/current_state.md"
    "docs/project_memory/current_truth.json"
    "docs/project_memory/current_truth.md"
)

$TrackedDeletionPaths = @(
    # Add exact tracked deleted or moved source paths here when applicable.
)

git add -- $AddPaths

if ($LASTEXITCODE -ne 0) {
    throw "Exact-file staging failed."
}

if ($TrackedDeletionPaths.Count -gt 0) {
    git add -u -- $TrackedDeletionPaths

    if ($LASTEXITCODE -ne 0) {
        throw "Tracked deletion or move-source staging failed."
    }
}

git status --short --untracked-files=all
git diff --cached --name-status
git diff --cached --check
```

Confirm only the accepted milestone files are staged before committing.

For moves or renames whose old tracked source lives beneath an ignored path, put the destination in `$AddPaths` and the old tracked source in `$TrackedDeletionPaths`. Do not use `-f` merely to stage a tracked deletion.

Verify rename mappings with `git diff --cached --name-status -M`. For a detected rename, `git diff --cached --name-only` normally reports the destination path rather than both source and destination, so do not compare that output against a list containing both sides of the rename.

## 12. Phase H — feature commit

```powershell
cd C:\projects\fitness_ai

git commit -m "{{FEATURE_COMMIT_MESSAGE}}"

if ($LASTEXITCODE -ne 0) {
    throw "Feature commit failed."
}

git status --short
git log --oneline -3
```

## 13. Phase I — feature push and local no-ff merge

```powershell
cd C:\projects\fitness_ai

git push -u origin {{FEATURE_BRANCH}}

if ($LASTEXITCODE -ne 0) {
    throw "Feature push failed."
}

git checkout main

if ($LASTEXITCODE -ne 0) {
    throw "Checkout of main failed."
}

git pull --ff-only origin main

if ($LASTEXITCODE -ne 0) {
    throw "Fast-forward pull of origin/main failed."
}

git merge --no-ff `
  {{FEATURE_BRANCH}} `
  -m "{{MERGE_MESSAGE}}"

if ($LASTEXITCODE -ne 0) {
    throw "No-ff merge failed."
}

$FeatureCommit = git rev-parse {{FEATURE_BRANCH}}

git merge-base --is-ancestor $FeatureCommit main

if ($LASTEXITCODE -ne 0) {
    throw "Accepted feature commit is not an ancestor of main."
}

Write-Host ""
Write-Host "Feature commit:"
git rev-parse --short {{FEATURE_BRANCH}}

Write-Host ""
Write-Host "Merged main:"
git rev-parse --short HEAD

Write-Host ""
Write-Host "Status:"
git status --short
```

Do not push `main` yet.

## 14. Phase J — merged-main automated validation

Architecture supplies milestone-specific targeted validation.

```powershell
cd C:\projects\fitness_ai

$DbPath = "C:\projects\fitness_ai\fitness_ai.db"
$DbHashBefore = (Get-FileHash $DbPath -Algorithm SHA256).Hash

{{TARGETED_MILESTONE_VALIDATION}}

.\.venv\Scripts\python.exe -m pytest `
  tests/test_project_memory_check.py `
  -q

.\.venv\Scripts\python.exe `
  tools\project_memory_check.py `
  --project-root .

git diff --check

$DbHashAfter = (Get-FileHash $DbPath -Algorithm SHA256).Hash

Write-Host ""
Write-Host "DB before: $DbHashBefore"
Write-Host "DB after:  $DbHashAfter"

if ($DbHashBefore -ne $DbHashAfter) {
    throw "Canonical fitness_ai.db changed during merged-main automated validation."
}

Write-Host ""
Write-Host "Status:"
git status --short
```

For frontend work normally include:

```powershell
cd C:\projects\fitness_ai\frontend

npm run lint
npm run build

cd C:\projects\fitness_ai
```

Use targeted tests instead of reflexively running the full suite.

The DB hash guard is meaningful only when no normal application process is concurrently writing to the canonical database.

## 15. Phase K — merged-main production smoke

For UI work, run the second production smoke from merged local `main`.

Architecture gives a tighter checklist focused on the primary feature, highest-risk regressions, persistence/refresh, relevant mobile/desktop states, themes, console/hydration warnings, and horizontal overflow.

The user reports `green`.

Do not push `main` until this passes.

## 16. Phase L — push main and snapshot

Only after merged-main validation and required smoke pass:

```powershell
cd C:\projects\fitness_ai

git status --short
git log --oneline -8

git push origin main

if ($LASTEXITCODE -ne 0) {
    throw "Final main push failed."
}

$commit = git rev-parse --short HEAD
$date = Get-Date -Format "yyyy-MM-dd"
$slug = "{{SNAPSHOT_SLUG}}"

$zip = "C:\projects\fitness_ai_external\snapshots\fitness_ai_snapshot_${date}_${commit}_main_${slug}.zip"

git archive `
  --format zip `
  --output $zip `
  HEAD

if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $zip)) {
    throw "Snapshot creation failed."
}

Write-Host ""
Write-Host "Snapshot created:"
Write-Host $zip
```

Acceptance-state docs belong in the feature commit. Do not create routine post-merge docs-only acceptance commits.

## 17. Phase M — final pasteback

```powershell
cd C:\projects\fitness_ai

Write-Host ""
Write-Host "Branch:"
git branch --show-current

Write-Host ""
Write-Host "Status:"
git status --short

Write-Host ""
Write-Host "Recent commits:"
git log --oneline -8

Write-Host ""
Write-Host "Local main:"
git rev-parse --short HEAD

Write-Host ""
Write-Host "Origin main:"
git rev-parse --short origin/main
```

Architecture confirms: branch `main`, clean working tree, local `main` equals `origin/main`, accepted feature commit exists, `--no-ff` merge commit exists, and snapshot was created from exact merged-main HEAD.

Then Architecture states that the milestone is fully closed.

## 18. Standard conversational rhythm

```text
Codex completion
→ Architecture gives cleanup + feature smoke
→ user reports green
→ Architecture accepts
→ Architecture gives acceptance-state commands
→ user validates and reports green
→ Architecture gives exact-file staging
→ staged set verified
→ Architecture gives commit/push/merge
→ merged-main automated validation
→ user reports green
→ Architecture gives merged-main smoke
→ user reports green
→ Architecture gives main push/snapshot
→ final pasteback
→ milestone closed
```

Do not turn this into one-command-at-a-time supervision.

Do not turn it into one giant script.

Use medium-sized phases with real risk gates.

## 19. Architecture-chat onboarding requirement

A newly onboarded Architecture chat must read:

```text
docs/project_memory/architecture_chat_bootstrap_template.md
docs/project_memory/architecture_milestone_closeout_command_template.md
```

before managing its first milestone closeout.

The bootstrap governs authority. This runbook governs the executable closeout ceremony.

Current explicit user instructions and higher-priority canonical authority always win.
