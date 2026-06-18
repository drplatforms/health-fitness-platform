# Development Workflow

Last updated: 2026-06-18

## Default project path

On Windows, assume project root:

```powershell
cd C:\projectsitness_ai
```

Patch and snapshot files are normally downloaded to this same project root.

## Before applying a patch

```powershell
git status --short
git log --oneline -5
```

Clean unrelated drift before applying feature work. Do not stage patch files, zip files, temporary artifacts, or local runtime outputs.

## Preferred validation order

For docs-only changes:

1. Confirm intended files changed.
2. Confirm no runtime code changed.
3. Run markdown/file existence checks manually if needed.

For code changes:

```powershell
ruff check . --fix
black .
.\.venv\Scripts\python.exe -m pytest <focused tests> -q
```

Then run broader focused suites and full pytest when practical.

## Commit hygiene

Before commit:

```powershell
git status --short
git diff --cached --name-only
```

Only intended files should be staged.

## Known pain point

Black may reformat unrelated test drift if local files are dirty. Clean unrelated unstaged drift before committing if it was not part of the milestone.
