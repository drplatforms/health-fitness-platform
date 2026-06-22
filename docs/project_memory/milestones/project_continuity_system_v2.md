# Project Continuity System v2

Status: AUTHORIZED FOR BACKEND / DEVOPS TOOLING IMPLEMENTATION

Branch: `feature/project-continuity-system-v2`

Previous accepted milestone: Daily Coach Async Provider Runtime Design v1

## Purpose

Create an active continuity/onboarding system for AI Health Coach / fitness_ai so new chats can rehydrate from repo truth without scattered transcript memory.

## Scope

- machine-readable project state
- role-specific bootstraps
- current workflow contract
- next milestone pointer
- onboarding self-test
- dev assistant continuity brief
- project-memory enforcement updates
- current state / handoff updates

## Non-goals

- no Daily Coach provider runtime
- no Daily Coach persistence
- no direct_ollama call
- no CrewAI call
- no qwen3 call
- no qwen3 bridge
- no qwen3:32b promotion
- no worker / queue / scheduler
- no DB schema
- no FastAPI behavior changes
- no Streamlit behavior changes
- no normal Today behavior changes
- no app/wapp command behavior changes
- no nutrition, workout, or report behavior changes
- no broad repo formatter churn

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
