# Project continuity bootstrap

Current implementation milestone: QA Seed Data Verification CLI v1

Branch: `feature/qa-seed-data-verification-cli-v1`

Previous accepted milestone: Runtime / DB Source Verification v1

Previous accepted commit: `6aaff41`

Current purpose:
Verify weekly-window-specific QA seed data outside Streamlit before rebuilding Weekly Coach Summary QA Date Range Debug v2.

Key commands:
- `python tools/dev_runtime_db_diagnostics.py`
- `python tools/dev_qa_seed_data_verification.py --start-date 2026-06-08 --end-date 2026-06-14`
- `python tools/dev_qa_seed_data_verification.py --start-date 2026-05-18 --end-date 2026-06-14`

Boundaries:
- no Streamlit UI change
- no Date-Range QA Debug panel
- no provider runtime
- no DB mutation
- no raw rows
