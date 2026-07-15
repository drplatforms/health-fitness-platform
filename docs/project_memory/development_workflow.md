# Development Workflow

The Health & Fitness Platform uses a local-first, validation-first workflow. Windows at `C:\projects\fitness_ai` owns canonical daily implementation and runtime. FastAPI on `8000` and the production Next.js frontend on `3100` are the primary product stack.

## Work sequence

1. Reconcile the authorized handoff with repository truth and the project-memory source hierarchy.
2. Verify base/branch/worktree safety and create the authorized feature branch.
3. Implement a narrow diff without disturbing unrelated work or the real database.
4. Run targeted automated checks, then risk-appropriate lint/build/compile validation.
5. For UI changes, run final production-mode browser smoke at `http://127.0.0.1:3100` using safe data and include console/mobile checks.
6. Update project memory and run memory validation.
7. Audit the complete diff, staged state, artifacts, and database safety.
8. Present the unstaged evidence for Architecture review unless a handoff explicitly authorizes further Git steps.

After Architecture acceptance and explicit authority, delivery continues through reviewed staging, feature commit/push, merge, ancestry verification, merged-main validation, main push, and snapshot.

## Environments

- **Windows canonical:** `C:\projects\fitness_ai`.
- **Linux secondary:** `~/projects/fitness-ai-platform`, optional for validation, runtime, or demos.
- **Streamlit:** Streamlit is legacy/developer-only; it is not the canonical UI or a default acceptance surface.
- **Next.js dev:** optional port `3000`; production build/runtime on `3100` is the user-facing acceptance surface.

Linux does not own routine runtime QA and does not require an automatic pull after snapshot. Use it only when the active milestone or user explicitly needs it.

## Roles and stops

The user owns intent and consequential authorization. Architecture owns scope, evidence requirements, actual-diff review, acceptance, and closeout direction. Codex owns bounded implementation and evidence, not self-acceptance or unilateral Git/external actions. Human QA owns final UI acceptance.

Stop on wrong branch/base, unexpected worktree changes, validation failure, real-database risk, material scope ambiguity, missing acceptance, or missing authority for an external/destructive action. Do not stop between safe mechanical commands already covered by the active phase.
