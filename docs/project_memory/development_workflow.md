# Development Workflow

Last updated: 2026-06-18

## Source-of-truth split

Windows is the source-of-truth development machine.

Use Windows for:

- git status, add, commit, push
- patch apply
- source edits
- docs/code validation before commit
- snapshot creation

Use Linux for:

- runtime API smoke checks
- Streamlit/FastAPI staging checks
- Ollama-connected runtime QA
- SQLite persisted-history inspection

Do not commit separately from Linux unless the milestone explicitly says to.

## Default project path

On Windows, assume project root:

```powershell
cd C:\projects\fitness_ai
```

Patch and snapshot files are normally downloaded to this same project root.

## Commit prep helper

Run the Windows helper from project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode full
```

Use `docs-only` for documentation and handoff-memory updates.

Use `code` when Python/app files changed. Pass focused tests when useful:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code -PytestArgs "tests/test_some_service.py","-q"
```

Use `full` before larger backend commits or when handoff asks for full validation.

## Docs-only validation path

For docs-only changes:

```powershell
git status --short
git diff --check
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode docs-only
```

Expected result:

- intended docs/tooling files only
- `docs/project_memory/` exists
- key project memory docs exist
- no runtime/product files changed
- no patch, zip, artifact, backup, or patched folders visible to git

Do not run Ruff or Black for docs-only work unless code files were intentionally changed.

## Code-change validation path

For code changes:

```powershell
git status --short
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode code
```

The code mode runs:

- `git diff --check`
- project memory existence checks
- `ruff check . --fix`
- `black .`
- focused pytest when `-PytestArgs` or touched test files are present

If no focused tests are detected, run the relevant pytest command manually or use full mode.

## Full validation path

For broad backend changes:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_commit_check.ps1 -Mode full
```

The full mode runs:

- `git diff --check`
- project memory existence checks
- `ruff check . --fix`
- `black .`
- `pytest -q`

## Patch and snapshot rules

Patch files should be downloaded to the project root and applied from there.

Example:

```powershell
cd C:\projects\fitness_ai
git apply .\some_patch.patch
```

Do not stage or commit:

- `*.patch`
- `*.zip`
- `artifacts/`
- `_backup_before_*/`
- `_patched_*/`
- `patch_check_output.txt`

Snapshot zips are transfer artifacts, not repo files.

Generated artifacts should not be staged unless a milestone explicitly asks for them.

Handoff docs under `docs/project_memory/handoffs/` are intentional repo files and must remain tracked.

## Local artifact ignores

Keep personal patch/snapshot ignores in `.git/info/exclude` when possible.

Recommended local excludes:

```gitignore
*.patch
*.zip
artifacts/
_backup_before_*/
_patched_*/
patch_check_output.txt
```

Use repo `.gitignore` only for broadly safe ignores. Do not add broad patterns that could hide intentional project files.

## Handling unrelated Black/Ruff drift

Before running Ruff or Black:

```powershell
git status --short
```

After running Ruff or Black:

```powershell
git status --short
git diff --name-only
```

If unrelated files changed, stop and inspect.

Do not commit unrelated formatting drift just because a formatter touched it.

If a change is definitely unrelated and you do not need it:

```powershell
git restore path\to\file.py
```

Use `git restore` only after confirming the file is not part of the current milestone.

## Before commit

```powershell
git status --short
git diff --cached --name-only
```

Only intended files should be staged.

For this project, normal commit prep is:

```powershell
git status --short
git add <intended files only>
git diff --cached --name-only
git commit -m "Your commit message"
git push
```
