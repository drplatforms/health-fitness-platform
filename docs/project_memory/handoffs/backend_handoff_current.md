# Backend Handoff Current

Current milestone: Project Continuity System v2

Status: DOCS + TOOLING / READY FOR ARCHITECTURE REVIEW

Branch: `feature/project-continuity-system-v2`

Previous accepted milestone: Daily Coach Async Provider Runtime Design v1

## Backend / DevOps status

Implemented an active continuity/onboarding system.

No backend product/runtime behavior was implemented.

## New first-read continuity files

- `docs/project_memory/project_state.json`
- `docs/project_memory/current_workflow_contract.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/chat_onboarding_test.md`
- role-specific bootstrap files

## New dev assistant command

```powershell
python tools/dev_assistant.py continuity-brief
```

## Backend workflow preserved

- phase-separated delivery
- temporary apply scripts outside repo, usually `C:\projects`
- run apply scripts from repo as `python ..\<script>.py`
- no `git add .`
- no broad formatters for docs-only work
- snapshot only after commit + push + clean tree
- Linux pull immediately after snapshot

## Expected validation

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
ruff check tools/dev_assistant.py tools/project_memory_check.py tests/test_project_memory_check.py
black --check tools/dev_assistant.py tools/project_memory_check.py tests/test_project_memory_check.py
python -m py_compile tools/dev_assistant.py tools/project_memory_check.py
```

## Preserved non-goals

- No provider runtime.
- No persistence implementation.
- No direct_ollama call.
- No CrewAI call.
- No qwen3 bridge.
- No worker / queue / scheduler.
- No DB schema.
- No FastAPI or Streamlit behavior changes.
- No normal Today behavior changes.
