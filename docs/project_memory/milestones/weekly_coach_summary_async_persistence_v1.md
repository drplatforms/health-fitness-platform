# Weekly Coach Summary Async Persistence v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: WEEKLY_COACH_SUMMARY_ASYNC_PERSISTENCE_V1_ACCEPTED

## Scope

This milestone adds safe persistence for deterministic Weekly Coach Summary approved outputs.

Implemented scope:

- Weekly Coach Summary persistence schema/table.
- Save approved deterministic summaries.
- Load persisted summary by id.
- Load latest approved summary by user/week.
- Deterministic fallback summary persistence.
- Duplicate policy: insert a new record and mark previous matching user/week/summary_version/context_version records stale.
- Sanitized metadata only.
- Developer Mode-only save/load controls in the existing Weekly Coach Summary inspection panel.

## Boundaries

No provider runtime was added.
No Ollama/CrewAI/qwen call was added.
No worker/queue/scheduler/polling was added.
No automatic weekly generation was added.
No API endpoint was added.
No public/default Weekly Coach Summary display was added.
No normal Today Weekly Coach Summary display was added.

## Persistence Safety

The persistence layer stores only ApprovedWeeklyCoachSummary-compatible public-safe display sections and sanitized metadata.

Forbidden persistence remains forbidden:

- raw provider output
- rejected provider output
- full prompt
- raw context
- scratchpad
- chain-of-thought
- secrets
- environment values
- stack traces
- tracebacks
- raw database rows
- provider debug internals

## Validation

Required validation:

- weekly coach summary model tests
- weekly coach summary service tests
- weekly coach summary persistence tests
- Streamlit Developer Mode tests
- project memory tests/checks
- developer preview command
- dev_commit_check -Mode code
- fsweep

## Next

Likely next milestone: Weekly Coach Summary Persistence QA / Developer Mode Smoke v1.
Alternative: Weekly Coach Summary Approved Preview Bridge Design v1.
