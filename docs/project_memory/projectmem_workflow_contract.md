# Projectmem Workflow Contract

## Purpose

Projectmem is an optional local acceleration layer for reducing repeated agent orientation and avoiding repeated historical mistakes. It supplements the repository's canonical context; it does not replace it.

## Authority

When information conflicts, use this order:

1. user product intent;
2. active Architecture handoff or other explicit authority;
3. `AGENTS.md`;
4. canonical `docs/project_memory/*`;
5. current repository truth;
6. Projectmem supplemental history and context.

Projectmem must not become a second authoritative roadmap, workflow, or acceptance ledger.

## Session-start usage

When Projectmem MCP tools are available, use them before broad repository rereading:

```text
get_summary()
get_project_map()
get_context(tokens≈1200, focus=<current milestone>)
```

Then read the active handoff and only the canonical files required by its scope, affected architecture contracts, and implementation area. Do not reread the entire project-memory corpus by default merely because it exists.

## High-signal write policy

Record durable, high-value information such as:

- real bugs or issues;
- failed or partial fix attempts;
- confirmed fixes;
- architecture and workflow decisions;
- recurring gotchas and workflow hazards.

Do not log routine successful edits, every command or test run, milestone ceremony, transient status chatter, or duplicated acceptance-ledger information. Do not fabricate failure history.

## Canonical project memory and intent

Acceptance state and strategic roadmap remain in `docs/project_memory/`. Projectmem's local `plan.md` is supplemental intent only and must not override `docs/project_memory/product_roadmap.md`, the active Architecture handoff, or user priority.

The entire `.projectmem/` directory remains local and Git-ignored. Generated events, summaries, maps, instructions, and plans must not be committed.

## Hooks and watcher

For Fitness AI, Projectmem Git hooks and the Projectmem watcher remain disabled unless Architecture explicitly authorizes a future bounded trial. Normal use is through MCP reads and writes, explicit CLI inspection, and manually curated high-signal events.

Do not run `pjm init`, install Projectmem hooks, start its watcher, or perform automatic Git-history backfill outside an authorized tooling milestone.

## Version and Windows usage

The validated integration version is `projectmem 0.2.0`. Future upgrades require a bounded compatibility review when behavior changes materially.

On the canonical Windows environment, run Projectmem with UTF-8 output enabled if the shell's default code page cannot render its Unicode CLI output:

```powershell
$env:PYTHONUTF8 = "1"
```

## Architecture onboarding

For a fresh Architecture chat, Projectmem may generate a compact temporary context artifact from local memory:

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null

$env:PYTHONUTF8 = "1"
.\.venv\Scripts\pjm.exe context --tokens 2500 |
    Set-Content tmp\projectmem_architecture_context.txt -Encoding utf8
```

The temporary export may accompany the latest repository snapshot, but it remains supplemental. The snapshot and canonical project memory remain authoritative. Delete the export after onboarding when it is no longer needed.
