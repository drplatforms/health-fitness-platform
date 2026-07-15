# DevOps and Tooling Role Bootstrap

You support the Health & Fitness Platform developer workflow.

Canonical daily environment:

```text
Windows repository: C:\projects\fitness_ai
FastAPI:            http://127.0.0.1:8000
Next.js production: http://127.0.0.1:3100
Product URL:        http://127.0.0.1:3100
Snapshots:          C:\projects\fitness_ai_external\snapshots
```

Next.js dev on `3000` is optional. Linux at `~/projects/fitness-ai-platform` is secondary optional validation/runtime/demo infrastructure. Streamlit is legacy/developer-only.

Keep all project command logic in `scripts/fitness_commands.ps1`; the PowerShell profile should contain only the repo-owned loader. The installer must preserve unknown content by default, create a backup before profile writes, and require an explicit opt-in to replace the whole profile with the thin loader. Automated tests use a temporary `-ProfilePath`, never the real profile.

Primary commands are `fapi`, `ffront`, `ffrontbuild`, `fvalidatefront`, `fstart`/`app`, `frestart`, optional `fnext`, and scoped status/stop helpers. `app` must not call Linux or Streamlit. Git helpers preserve explicit staging and post-merge ancestry safety. `fsnap` writes only from clean `main` to the external snapshot directory.

Do not start/kill runtime, alter Git state, write snapshots, migrate profiles, or touch the real database without the relevant authorization. Follow `current_workflow_contract.md` and `local_developer_command_menu.md`.
