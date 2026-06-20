# Daily Coach Narrative Same-Session Approved Preview Bridge v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Scope

This milestone adds a manual same-session bridge from developer-gated Daily Coach Narrative preview output to the normal Today Coach Note display.

The bridge is intentionally constrained:

- normal Today load remains deterministic
- provider preview remains manual and Developer Mode gated
- approval requires parse success and validation success
- rejected preview output cannot be approved
- approved text is stored only in Streamlit session state
- no database, report, file, or cache persistence is added
- provider output may replace only the coach note text
- Daily Next Action, CTA, workflow target, and backend-owned facts remain deterministic

## User-facing behavior

Normal Today continues to show the deterministic Today Coach Note immediately.

When Developer Mode is enabled and a provider preview validates successfully, the developer may choose **Approve for this session**. The approved note may then appear in the Today Coach Note area for the current session only.

A **Revert to deterministic note** action clears the session approval.

## Boundaries preserved

- no provider call on normal Today load
- no provider default change
- no qwen3:8b or qwen3:32b promotion
- no persistence or schema changes
- no report persistence change
- no Daily Next Action selection change
- no nutrition, workout, catalog, or report behavior change
- no raw or rejected provider output displayed in normal UI
