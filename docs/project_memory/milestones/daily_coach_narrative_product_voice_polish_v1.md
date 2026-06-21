# Daily Coach Narrative Product Voice Polish v1

Status: IMPLEMENTED / READY FOR LOCAL VALIDATION AND MANUAL QA

Branch: `feature/daily-coach-narrative-product-voice-polish-v1`

## Purpose

Improve the approved Daily Coach provider narrative quality while preserving the accepted same-session bridge safety boundary.

The target remains:

> sound right and be right.

This milestone improves qwen2.5:3b coach-note prompt guidance and adds stricter product-voice validation for generic, template-like, meta, hype, or unsupported copy.

## Approved scope implemented

- Refined the Daily Coach Narrative provider prompt to aim for a compact practical coach note.
- Added product voice guidance for qwen2.5:3b output shape.
- Added stricter validator rejection for generic/template/meta copy.
- Preserved unsupported-claim rejection and invented numeric checks.
- Added focused product voice regression tests.
- Updated project memory to record the voice polish boundary.

## Product voice target

Approved provider copy should be:

- clear
- direct
- calm
- specific
- human
- lightly encouraging
- action-oriented
- grounded in approved facts only
- concise enough for Today UI

The approved note should answer:

1. What matters today?
2. Why does the selected Daily Next Action make sense?
3. What is the lowest-friction next step?
4. What should the user avoid overthinking?

## Safety boundaries preserved

- `qwen2.5:3b` remains the bridge baseline only.
- `qwen2.5:3b` is not promoted to product default.
- No qwen3 model is bridge-enabled.
- No model is promoted.
- No provider default changed.
- No provider call occurs on normal Today load.
- Provider preview remains manual Developer Mode only.
- Approval remains explicit and manual.
- Approval remains session-only.
- Approved provider narrative does not persist.
- No DB write, report write, file write, or schema change is added.
- Daily Next Action, nutrition, workout, catalog, and report behavior are unchanged.
- Raw/rejected provider output remains hidden from normal UI.
- Provider/model/debug internals remain hidden from normal UI.

## Not implemented

- No automatic approval.
- No normal-load AI.
- No provider persistence.
- No async provider generation.
- No RAG/vector/MoE/MCP implementation.
- No frontend rewrite.
- No qwen3 bridge use.

## Validation focus

Focused validation should prove:

- improved product voice prompt guidance exists
- specific grounded copy remains approvable
- generic/template/meta copy is rejected or flagged
- unsupported claims remain blocked
- same-session bridge model policy is unchanged
- project memory includes this milestone
