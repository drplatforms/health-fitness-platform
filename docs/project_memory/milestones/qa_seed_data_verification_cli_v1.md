# QA Seed Data Verification CLI v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Branch: `feature/qa-seed-data-verification-cli-v1`

This milestone adds a read-only CLI and service that verify seeded QA data outside Streamlit.

Scope:
- active database path/connectability is surfaced through the CLI output
- QA users 101-105 are checked
- global per-domain seed bounds are reported
- selected weekly-window counts are reported
- data-quality and diagnosis labels are generated for debug use only

Non-goals:
- no Streamlit UI changes
- no Date-Range QA Debug panel
- no encoding/mojibake cleanup
- no data reseeding or mutation
- no provider runtime, Ollama, CrewAI, qwen, worker, queue, scheduler, or automatic generation

Default verification window:
- 2026-06-08 through 2026-06-14

Additional required verification window:
- 2026-05-18 through 2026-06-14
