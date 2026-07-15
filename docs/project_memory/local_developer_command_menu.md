# Local Developer Command Menu

The repo-owned PowerShell command menu is `scripts/fitness_commands.ps1`. It implements the Windows-first Health & Fitness Platform workflow and must be the only location for project command logic. A user profile should contain only a thin loader.

## Install and reload

The safe default installer preserves unknown profile content, removes recognized prior managed blocks, creates a timestamped backup when a profile exists, and installs one managed loader:

```powershell
& "C:\projects\fitness_ai\scripts\install_fitness_commands_profile.ps1"
. $PROFILE
```

For a deliberately simplified profile, use the explicit opt-in only after reviewing the backup behavior:

```powershell
& "C:\projects\fitness_ai\scripts\install_fitness_commands_profile.ps1" -ReplaceProfileWithThinLoader
```

The installer supports `-ProfilePath` for safe temporary-file validation. Automated validation must never target the real `$PROFILE`.

## Primary Windows runtime

| Command | Meaning |
| --- | --- |
| `cdf` | Enter `C:\projects\fitness_ai`, set `PYTHONPATH`, and activate `.venv` when available. |
| `cdff` | Enter the `frontend` directory. |
| `fapi` | Start `python -m uvicorn api.main:app` on `127.0.0.1:8000` in a hidden process. |
| `ffront` | Start an existing production Next.js build on port `3100`; fail clearly when `.next` is absent. |
| `ffrontbuild` | Stop only repo-scoped production frontend processes, build, and start production Next.js. |
| `fvalidatefront` | Run frontend lint and production build without starting a server. |
| `fstart` / `app` | Start FastAPI and the existing production frontend build. `app` never invokes Linux or Streamlit. |
| `frestart` | Stop repo-scoped product processes and restart the primary runtime without rebuilding. |
| `fnext` / `fnextfg` | Optional background/foreground Next.js development server on port `3000`. |
| `fopen` | Open the canonical product URL, `http://127.0.0.1:3100`. |
| `fports` | Show FastAPI `8000`, production Next.js `3100`, optional Next.js dev `3000`, and optional Ollama `11434`. |
| `wstatus` / `wstop` | Inspect or stop only verified repository-owned runtime listeners/process trees. |

`fapi`, `ffront`, `fnext`, and `fnextfg` refuse to create a duplicate when their expected port is already occupied. Stop helpers inspect the listener PID and parent chain, require both repository-path and expected-command evidence, and refuse to kill an unverified process. `wapp` remains a compatibility alias for `fstart` and emits a migration warning. Streamlit is legacy/developer-only. Streamlit is not started by any primary command.

## Git and delivery helpers

- `fpull` fetches/prunes origin, switches to clean `main`, pulls `origin main` with `--ff-only`, verifies local `main == origin/main`, and shows status/history. `gsync` is its compatibility alias.
- `gstate`, `fports`, and `fdoctor` are non-destructive inspection helpers.
- `gcheck [-Mode docs-only|code|full]` runs `git diff --check`, the supported `scripts/dev_commit_check.ps1` mode, the project-memory checker/tests, and developer-assistant memory/stale-document checks. It does not stage files.
- `gacp -Message <message>` never stages files and refuses `main` by default. `-AllowMain` is an explicit reviewed escape hatch.
- `fbranch <name>` requires a clean tree, fetches origin, fast-forwards `main`, verifies local `main == origin/main`, then creates the feature branch.
- `fmerge <feature-branch> <accepted-final-commit>` requires a clean/up-to-date `main`, performs a non-fast-forward merge, and verifies that the exact Architecture-accepted final commit—not merely the moving branch tip—is an ancestor of `main`. This is the required post-merge ancestry guard.
- `fsweep` scans tracked repository content for citation/tracking/placeholder contamination. `fbranches` separately lists branches already merged into `main`.
- `fsnap <slug>` requires clean `main`, validates a lowercase kebab-case slug, and writes the Git archive to `C:\projects\fitness_ai_external\snapshots`.
- `fmem` runs the project-memory checker, developer-assistant `memory-check`, `stale-doc-check`, and `continuity-brief`, plus project-memory pytest.

## Secondary Linux helpers

Linux is secondary. `lpull`, `lstatus`, `lsetup`, `lvalidate`, `lollama`, and `lsh` support optional Linux validation/runtime/demo work at `~/projects/fitness-ai-platform`. They are not invoked by primary Windows commands, and a Linux pull is not automatically required after a snapshot.

## Safety boundaries

Starting/stopping runtime, changing Git state, writing snapshots, or replacing a real profile requires the relevant user authority. Do not use helper smoke tests to start or kill live processes. Do not initialize or mutate `fitness_ai.db` while validating this command layer.
