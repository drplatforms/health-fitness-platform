# Current Workflow Contract

Last updated: 2026-06-22

## Purpose

This is the canonical operating contract for AI Health Coach / fitness_ai delivery work.

It preserves the successful old-chat workflow and the current backend process flow so future chats do not drift.

## Core Operating Principles

- Do not infer project rules from memory alone.
- Read repo docs and current project memory before exact implementation instructions.
- Use phase-separated delivery.
- Every phase has one purpose.
- Do not bundle branch/apply/validate/stage/commit/push/snapshot/Linux pull into one giant block.
- Do not ask Dustin to paste output after every successful phase.
- Ask for output only when something fails, state is unclear, or scope must be confirmed.
- Never use `git add .`.
- Always stage explicit intended files.
- Docs/project memory are first-class Definition of Done.
- Long handoffs belong in one copy/paste-ready code block.

## Runtime Model to Preserve

Windows owns source-of-truth repo work:

- repo path: `C:\projects\fitness_ai`
- Git orchestration
- branch creation
- patch apply
- commit
- push
- snapshot creation
- Ollama host

Linux owns canonical runtime/staging QA:

- repo path: `~/projects/fitness-ai-platform`
- tmux sessions: `fitness-api` and `fitness-ui`
- FastAPI + Streamlit runtime
- Linux runtime uses Windows Ollama over LAN

Command truth:

- `app` launches/manages the Linux FastAPI + Streamlit runtime.
- `wapp` is Windows-local only.
- `fports` is Windows-side ports only.

## Patch / Apply Artifact Location Rule

Temporary apply scripts and patch files live outside the repo.

Correct location:

`C:\projects`

Correct run pattern from repo root:

`python ..\<script>.py`

Raw patch pattern from repo root:

`git apply --check ..\<patch>.patch`

`git apply ..\<patch>.patch`

Do not place temporary apply scripts in `C:\projects\fitness_ai` because untracked repo-root scripts trip clean-tree guards.

Do not commit apply scripts, patch files, snapshots, qa_artifacts, database files, `.env`, secrets, or temp files.

## Standard Phase Flow

1. PHASE 1 — PREFLIGHT / BRANCH ONLY
2. PHASE 2 — APPLY ONLY
3. PHASE 3 — VALIDATE ONLY
4. PHASE 4 — MANUAL SMOKE ONLY, IF APPLICABLE
5. PHASE 5 — STAGE ONLY
6. PHASE 6 — COMMIT ONLY
7. PHASE 7 — PUSH ONLY
8. PHASE 8 — SNAPSHOT ONLY
9. PHASE 9 — LINUX PULL
10. PHASE 10 — LINUX RUNTIME RESTART, ONLY IF CODE/UI/RUNTIME CHANGED
11. PHASE 11 — HANDOFF

## Phase 1 — Preflight / Branch Only

Purpose: create the correct feature/hotfix branch from the expected baseline without touching files.

Typical commands:

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1

git fetch origin --prune
git switch main
git pull --ff-only origin main

if ((git rev-parse main) -ne (git rev-parse origin/main)) {
    throw "STOP: local main does not match origin/main"
}

git switch -c <branch>

git status -sb
git log --oneline --decorate -5
```

Use an exact expected baseline commit when the authorization provides one.

## Phase 2 — Apply Only

Purpose: apply the patch/script and inspect changed files.

```powershell
cd C:\projects\fitness_ai

if ((git branch --show-current) -ne "<expected_branch>") {
    throw "STOP: wrong branch."
}

if (-not (Test-Path ..\<apply_script>.py)) {
    throw "STOP: apply script missing from C:\projects."
}

if ((git status --porcelain) -ne $null) {
    git status --short
    throw "STOP: working tree is dirty before apply."
}

python ..\<apply_script>.py

Remove-Item ..\<apply_script>.py -Force

git status --short
git diff --name-only
git diff --stat
```

Every apply phase should include an expected changed-files list.

## Phase 3 — Validate Only

Docs-only / design-only:

```powershell
git diff --check

pytest tests/test_project_memory_check.py -q

python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/project_memory_check.py
python tools/dev_assistant.py continuity-brief

. .\scripts\fitness_commands.ps1
fsweep

scripts/dev_commit_check.ps1 -Mode docs-only
```

Code/UI/API/service:

```powershell
git diff --check

pytest <focused tests> -q
pytest tests/test_project_memory_check.py -q

python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check

. .\scripts\fitness_commands.ps1
fsweep

scripts/dev_commit_check.ps1 -Mode code

python -m py_compile <changed_python_files>
```

Validation failure means stop.

## Formatter Rules

Do not run broad formatters for docs-only work.

Forbidden for docs-only unless explicitly authorized:

- `black .`
- `ruff check . --fix`

If Python tooling files changed during docs/tooling work, use targeted checks:

```powershell
ruff check tools/dev_assistant.py tools/project_memory_check.py tests/test_project_memory_check.py
black --check tools/dev_assistant.py tools/project_memory_check.py tests/test_project_memory_check.py
python -m py_compile tools/dev_assistant.py tools/project_memory_check.py
```

## Phase 4 — Manual Smoke Only

Manual smoke is separate from validation.

Command-menu smoke:

```powershell
cd C:\projects\fitness_ai
. .\scripts\fitness_commands.ps1
fitness
```

Confirm:

- `app` = Linux canonical app runtime
- `wapp` = Windows-local only
- `fports` = Windows-side ports only

Runtime smoke only when ready:

```powershell
app
lstatus
```

## Phase 5 — Stage Only

Never use `git add .`.

Use explicit files only:

```powershell
git add <file1>
git add <file2>
git add <file3>

git status --short
git diff --cached --stat
```

## Phase 6 — Commit Only

```powershell
git commit -m "<message>"

git status -sb
git log --oneline --decorate -5
```

Do not snapshot in the commit phase.

## Phase 7 — Push Only

```powershell
git push -u origin <branch>

git status -sb
git log --oneline --decorate -5
```

## Phase 8 — Snapshot Only

Snapshot only after commit and push succeed.

```powershell
$commit = git rev-parse --short HEAD

if ((git status --porcelain) -ne $null) {
    git status --short
    throw "STOP: working tree is not clean. Do not snapshot yet."
}

$date = Get-Date -Format "yyyy-MM-dd"
$commitMessage = git log -1 --pretty=%s
$safeMessage = $commitMessage -replace '[^a-zA-Z0-9]+', '-'
$safeMessage = $safeMessage.ToLower().Trim('-')
$zipName = "..\fitness_ai_snapshot_${date}_${commit}_${safeMessage}.zip"

git archive --format=zip --output=$zipName HEAD

Get-Item $zipName
```

Do not commit the snapshot.

## Phase 9 — Linux Pull

Linux pull happens immediately after snapshot.

```bash
cd ~/projects/fitness-ai-platform
source .venv/bin/activate

git fetch origin --prune
git switch <branch> || git switch --track origin/<branch>
git pull --ff-only origin <branch>

git status -sb
git log --oneline --decorate -10
```

## Phase 10 — Linux Runtime Restart, If Needed

Restart only if code/UI/runtime changed.

```bash
tmux kill-session -t fitness-api 2>/dev/null || true
tmux kill-session -t fitness-ui 2>/dev/null || true

cd ~/projects/fitness-ai-platform

tmux new-session -d -s fitness-api 'source .venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8000'
tmux new-session -d -s fitness-ui 'source .venv/bin/activate && streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8501'

tmux ls
```

Docs-only/design-only usually does not need runtime restart.

## Phase 11 — Handoff

Handoff comes after commit, push, snapshot, Linux pull, and runtime restart if applicable.

Handoff must include:

- recipient
- project
- branch
- milestone
- status
- proposed final status
- commit
- snapshot
- Linux pull status
- runtime restart status if applicable
- files changed
- validation
- delivery
- boundary confirmation
- next milestone recommendation

Long handoffs must be in one copy/paste-ready code block.

## Error Handling / Git Safety

If Git state is unclear, do diagnostics only.

Do not run until state is understood:

- `git reset --hard`
- `git stash`
- `git clean -fd`
- `git merge`
- `git pull`

Create rescue patches before destructive correction:

```bash
git diff > ~/rescue_working_diff.patch
git diff --cached > ~/rescue_staged_diff.patch
```

## Scope Matching by Milestone Type

Docs-only / design-only:

- docs/project_memory
- design docs
- handoffs
- open questions
- project memory checker/tests if needed
- no runtime restart required

Backend/API/service:

- in-scope services/models/API
- focused tests
- project memory updates
- runtime restart likely required after Linux pull

Streamlit/UI:

- UI files
- UI-focused tests
- py_compile Streamlit
- manual Streamlit smoke
- runtime restart required after Linux pull

DevOps/tooling:

- command scripts
- tooling docs
- focused tooling tests
- manual command menu smoke

Provider/model:

- only if Architecture explicitly authorizes
- strict parser
- validator
- deterministic fallback
- no raw provider output in normal UI

## Provider / Model Policy

- qwen2.5:3b is bridge baseline only.
- qwen3 is not bridge-enabled.
- qwen3:32b is research / future premium async candidate only.
- No model is promoted without Architecture approval.
- Deterministic fallback remains mandatory.
- Validation must not be loosened to make a model pass.

## Daily Coach Async Current Boundary

Current accepted boundary:

- async contracts
- service shell
- developer-only lifecycle prototype
- provider runtime design

Not authorized:

- provider runtime implementation
- direct_ollama Daily Coach async runtime
- CrewAI Daily Coach async runtime
- qwen3 bridge
- qwen3/qwen3:32b promotion
- worker / queue / scheduler
- DB persistence
- normal Today provider call
- public async narrative display

## Compact Default Command Template

```powershell
cd C:\projects\fitness_ai
.\.venv\Scripts\Activate.ps1
git fetch origin --prune
git switch main
git pull --ff-only origin main
git switch -c <branch>

python ..\<apply_script>.py
Remove-Item ..\<apply_script>.py -Force

git diff --check
pytest tests/test_project_memory_check.py -q
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/project_memory_check.py
python tools/dev_assistant.py continuity-brief
. .\scripts\fitness_commands.ps1
fsweep
scripts/dev_commit_check.ps1 -Mode <docs-only|code>

git add <explicit files only>
git commit -m "<message>"
git push -u origin <branch>
```

Then snapshot and Linux pull immediately.
