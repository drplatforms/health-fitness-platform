# Health & Fitness Platform Repository Instructions

## Product Boundaries

- Build a local-first personal health and fitness platform that is data-first and reliable without generative AI.
- Backend services own validated facts, calculations, constraints, persistence, and fallback behavior.
- Optional AI or provider features may propose, explore, or explain, but must not silently override validated product data or make unsupported health decisions.
- Preserve source and decision provenance where it matters.
- Reuse existing services, contracts, models, helpers, and UI patterns where practical.
- Keep the product compact, practical, and focused on useful daily workflows.
- Do not add provider systems, RAG, embeddings, vector search, or autonomous agent orchestration unless the user's current request actually requires them.
- Do not add parallel assistant-specific instruction files such as `CLAUDE.md`.

## Working Rules

- Work from the user's current explicit request and the repository itself.
- An explicit implementation request from the user is authorization for that scoped work.
- Inspect the current branch, Git status, relevant diff, and only the code needed for the task before editing.
- Briefly state what existing implementation you found and your intended approach, then proceed unless there is a meaningful conflict.
- Preserve unrelated and uncommitted work. Never reset, restore, discard, or destructively clean work you did not create.
- Modify only what the task requires. Prefer narrow patches and avoid unrelated refactors or formatting churn.
- Repository truth and the user's current explicit direction outrank stale planning or historical documentation.
- Project memory and Projectmem are not routine onboarding requirements. Consult them only when the task directly changes them or when a concrete historical ambiguity, prior failure, or unresolved decision makes them useful.
- Do not perform mandatory Projectmem orientation, logging, or project-memory updates for ordinary feature work.
- Do not stop scoped implementation merely because an old milestone, handoff, or current-state pointer has not been updated.
- Add dependencies, routes, schema changes, persistence, or new infrastructure only when the requested feature genuinely requires them. Treat meaningful scope expansion as something to surface, not something to hide.

## Data Safety

- Never mutate, replace, or commit the user's real `fitness_ai.db` during automated validation or smoke testing.
- Use disposable databases or copies for automated mutation.
- Preserve real user data and remove temporary artifacts created during the task.

## Validation

- Use targeted, risk-based validation appropriate to the actual change.
- Run affected tests and the nearest useful regression coverage.
- Run lint, build, and browser smoke only when relevant to the changed surface and risk.
- User-visible frontend changes should receive a practical browser smoke check at an appropriate desktop and mobile width.
- Do not run project-memory checks unless project-memory files changed.
- Do not run the full repository test suite by default. Use it only for genuinely cross-cutting risk or when explicitly requested.
- Inspect the final diff, Git status, and temporary artifacts before reporting completion.
- Never claim validation that was not actually performed.

## Git

- Stage, commit, or push only when explicitly authorized.
- Never merge to `main`; the user owns the final merge.
- Never force-push, rewrite history, delete branches, or discard unrelated work without explicit authorization.
- Do not create snapshots by default.

## Completion

Report:
- what changed;
- validation actually performed;
- any real unresolved issue or limitation;
- relevant Git status.

Do not dump exhaustive command histories, Projectmem orientation reports, or routine process telemetry unless specifically requested.
