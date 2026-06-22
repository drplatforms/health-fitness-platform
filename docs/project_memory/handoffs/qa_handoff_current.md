# QA Handoff Current

Updated: 2026-06-21

## Current Accepted Milestone

Daily Coach Async Contracts + Data Model v1 is accepted.

## QA-Relevant Coverage

Accepted tests cover:

- required async job statuses
- model lane policy
- context identity creation
- deterministic context hash behavior
- hash stability across dictionary ordering
- hash changes for meaningful context changes
- sanitized diagnostics contract
- qwen2.5:3b bridge baseline policy
- qwen3:32b premium async candidate / research-only policy
- qwen3 not bridge-approved

## Command Menu Hotfix Boundary

QA should continue checking that:

- `app` means Linux runtime
- `wapp` means Windows-local runtime
- `fports` is Windows-side ports only
- Linux tmux runtime remains canonical

## Future QA for Next Milestone

Daily Coach Async Service Shell / No Worker v1 should test:

- create/read/latest behavior
- stale job rejection
- context identity matching
- deterministic fallback availability
- no provider execution
- no normal Today provider call
- no UI display behavior change
