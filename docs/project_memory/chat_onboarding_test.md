# Chat Onboarding Self-Test

Last updated: 2026-06-22

Every new Architecture, Backend, QA, DevOps/Tooling, Streamlit UI, AI Provider Integration, or Project Memory chat should answer these before authorizing work or producing patches.

## Questions

1. What is the latest accepted milestone?
2. What is the latest accepted status?
3. What branch is source of truth?
4. What is the next recommended milestone?
5. What is not authorized?
6. What is the current Windows/Linux runtime split?
7. What is the current model/provider policy?
8. What is the current Daily Coach async boundary?
9. What workflow style should commands follow?
10. Where should temporary apply scripts and patches live?
11. Should long handoffs be inside code blocks?
12. Should docs-only work run `black .` or `ruff check . --fix`?
13. When should merge commands be provided?
14. When should Linux pull commands be provided?
15. What files must a new Backend chat read first?

## Expected answers

1. Latest accepted milestone: Daily Coach Async Provider Runtime Design v1.
2. Latest accepted status: `DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED`.
3. Source of truth branch: `main`.
4. Current authorized milestone: Project Continuity System v2. Recommended next after acceptance: Daily Coach Async Persistence Design v1.
5. Not authorized: provider runtime, direct_ollama Daily Coach async runtime, CrewAI Daily Coach async runtime, qwen3 bridge/promotion, qwen3:32b promotion, worker, queue, scheduler, DB persistence implementation, normal Today provider call, public async narrative display.
6. Windows is source-of-truth development/control machine; Linux is canonical FastAPI + Streamlit runtime.
7. qwen2.5:3b is bridge baseline only; qwen3 is not bridge-enabled; qwen3:32b is research / future premium async candidate only; deterministic fallback remains mandatory.
8. Daily Coach async has contracts, service shell, developer-only lifecycle prototype, and provider runtime design; no provider runtime or public async display yet.
9. Commands should follow phase-separated delivery using old-chat-sized operational blocks.
10. Temporary apply scripts and patches live outside the repo, usually `C:\projects`.
11. Yes. Long handoffs must be in one copy/paste-ready code block.
12. No. Docs-only work should not run `black .` or `ruff check . --fix`.
13. Merge commands should be provided only when merge is actually the next action.
14. Linux pull commands should be provided immediately after snapshot.
15. Backend must read `project_state.json`, `project_continuity_bootstrap.md`, `current_workflow_contract.md`, `next_milestone.md`, `current_state.md`, current handoffs, and active Architecture authorization before implementation.
