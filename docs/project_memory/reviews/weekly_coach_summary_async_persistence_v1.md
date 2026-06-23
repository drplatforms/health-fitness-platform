# Weekly Coach Summary Async Persistence v1 Review

Final status requested: WEEKLY_COACH_SUMMARY_ASYNC_PERSISTENCE_V1_ACCEPTED

## Summary

Weekly Coach Summary Async Persistence v1 adds safe persistence for deterministic Weekly Coach Summary approved outputs.

The implementation persists only ApprovedWeeklyCoachSummary-compatible public-safe sections and sanitized metadata, supports save/load by id, latest approved retrieval by user/week, deterministic fallback persistence, and stale-on-new-save duplicate handling.

## Accepted Boundary

- approved summary persistence implemented
- deterministic fallback persistence implemented
- latest approved retrieval implemented
- sanitized metadata only
- Developer Mode-only save/load controls added
- normal/default UI unchanged
- normal Today unchanged
- no public/default display added
- no provider runtime added
- no Ollama/CrewAI/qwen call added
- no worker/queue/scheduler/polling added
- no automatic generation added

## Forbidden Fields Remain Forbidden

No raw provider output persisted.
No rejected provider output persisted.
No prompt/raw context/scratchpad persisted.
No stack traces, secrets, environment values, raw database rows, or provider debug internals persisted.

## Duplicate Policy

V1 inserts a new record and marks previous matching user/week/summary_version/context_version records stale. Latest-approved retrieval ignores stale and expired records.

## Next Recommendation

Weekly Coach Summary Persistence QA / Developer Mode Smoke v1 should prove the save/load path on the Linux runtime before any public/default preview bridge is considered.
