# QA Handoff Current

Current milestone: Project Continuity System v2

Status: DOCS + TOOLING / READY FOR QA REVIEW

Branch: `feature/project-continuity-system-v2`

Previous accepted milestone: Daily Coach Async Provider Runtime Design v1

## QA focus

QA should verify this is a docs + tooling continuity milestone only.

## Expected artifacts

- `docs/project_memory/project_state.json`
- `docs/project_memory/role_bootstrap_architecture.md`
- `docs/project_memory/role_bootstrap_backend.md`
- `docs/project_memory/role_bootstrap_qa.md`
- `docs/project_memory/role_bootstrap_devops_tooling.md`
- `docs/project_memory/current_workflow_contract.md`
- `docs/project_memory/next_milestone.md`
- `docs/project_memory/chat_onboarding_test.md`
- `python tools/dev_assistant.py continuity-brief`

## QA checks

- continuity files exist
- `project_state.json` is valid JSON
- role bootstraps preserve lane-specific responsibilities
- workflow contract includes phase-separated delivery
- workflow contract forbids `git add .`
- workflow contract forbids broad formatters for docs-only work
- workflow contract documents temporary apply artifacts in `C:\projects`
- workflow contract requires Linux pull after snapshot
- model/provider policy is preserved
- Daily Coach async boundary is preserved

## Runtime behavior expected

Runtime behavior should remain unchanged.

No manual runtime QA is required unless Architecture requests it.

## Boundary checks

- no provider runtime
- no persistence implementation
- no direct_ollama call
- no CrewAI call
- no qwen3 bridge
- no worker / queue / scheduler
- no DB schema
- no FastAPI behavior change
- no Streamlit behavior change
- no normal Today behavior change
- no app/wapp command behavior change
