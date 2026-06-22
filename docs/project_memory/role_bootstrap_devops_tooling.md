# Role Bootstrap — DevOps / Tooling

Last updated: 2026-06-22

## Purpose

Use this file to onboard a new DevOps / Tooling chat for AI Health Coach / fitness_ai.

## Runtime split

Windows is the source-of-truth development/control machine.

Windows owns:

- Git orchestration
- branch creation
- patch apply
- commit
- push
- snapshot creation
- Ollama host

Linux is the canonical FastAPI + Streamlit runtime.

Linux runtime repo:

`~/projects/fitness-ai-platform`

Linux tmux sessions:

- `fitness-api`
- `fitness-ui`

Linux runtime uses Windows Ollama over LAN.

## Command truth

- `app` launches/manages Linux FastAPI + Streamlit runtime.
- `wapp` is Windows-local only.
- `fports` is Windows-side ports only.

Do not confuse `app` and `wapp`.

Do not treat old Windows-local Streamlit behavior as canonical runtime.

## Command-menu changes

Command-menu changes require:

- focused command-menu tests
- project memory updates
- manual `fitness` menu smoke
- confirmation that `app`, `wapp`, and `fports` labels remain correct
- `fsweep` clean

## Linux Git safety

Do not reset/stash/clean on Linux unless diagnosing a dirty tree and preserving work first.

If Linux Git state is unclear, run diagnostics only:

- `git status -sb`
- `git fetch origin --prune`
- `git branch -vv`
- `git log --oneline --decorate --graph --all -15`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git ls-files --others --exclude-standard`

## Runtime restart rule

Restart Linux runtime after code/UI/runtime changes are pulled to Linux.

Docs-only/design-only changes generally do not require runtime restart unless the user asks.
