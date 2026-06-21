# Daily Coach Narrative Product Voice Polish v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW AFTER LOCAL QA

Proposed final status:

`DAILY_COACH_NARRATIVE_PRODUCT_VOICE_POLISH_V1_ACCEPTED`

## Review summary

Daily Coach Narrative Product Voice Polish v1 improves the approved Daily Coach provider narrative inside the existing manual same-session bridge.

The change makes qwen2.5:3b prompt guidance more product-like and adds stricter copy validation so generic/template/meta language is rejected rather than accepted just because it parses.

## Voice polish implemented

- Added a `PRODUCT_VOICE_TARGET` block to the provider prompt.
- Changed the example coach note away from a terse system-style line and toward a practical two-to-three-sentence coach note.
- Added explicit prompt guidance to avoid hype, fake intimacy, generic filler, and meta phrasing.
- Added validator rejection for generic/template phrases such as:
  - `based on the data provided`
  - `based on the information provided`
  - `you got this`
  - heading-like labels such as `what matters today:` and `why it matters:`
- Added focused product voice tests for prompt shape, grounded approved copy, generic/template rejection, unsupported-claim rejection, bridge model policy, and project-memory documentation.

## Boundary confirmation

- qwen2.5:3b remains bridge baseline only.
- qwen2.5:3b is not promoted to product default.
- qwen2.5:7b is not bridge-enabled.
- qwen3:8b is not bridge-enabled.
- qwen3:14b is not bridge-enabled.
- qwen3:32b is not bridge-enabled.
- qwen3:30b-a3b is not bridge-enabled.
- No model is promoted.
- No provider default changed.
- No provider call occurs on normal Today load.
- Provider preview remains manual Developer Mode only.
- Approval remains manual.
- Approval remains session-only.
- Approved provider narrative does not persist.
- No DB write.
- No report write.
- No file write.
- No schema change.
- No Daily Next Action change.
- No nutrition calculation change.
- No workout generation/lifecycle change.
- No catalog change.
- No validation loosening.
- Unsupported claims remain blocked.
- Generic/meta copy is blocked or flagged.
- Raw/rejected provider output is not displayed.
- Provider/model/debug internals are not displayed in normal UI.
- Developer Mode diagnostics remain sanitized.
- No PyArrow diagnostic rendering change was introduced.
- Docs/project memory updated.
- No qa_artifacts or snapshots should be committed.
- Workflow contract and script safety addendum remain in force.

## Required local/manual QA before final acceptance

Manual QA should run on Windows with FastAPI, Streamlit, and local Ollama using `qwen2.5:3b`.

Acceptance should confirm:

- normal Today load remains deterministic
- no provider call occurs on normal Today load
- qwen2.5:3b Developer Mode preview can approve
- approved narrative reads more product-grade and remains grounded
- session approval displays the improved note
- no provider/debug leak appears in normal UI
- no raw/rejected output appears
- no persistence occurs
- qwen3 remains not bridge-enabled
- no PyArrow diagnostic issue appears
