# Open Questions — Daily Coach Wide Context Copy Cleanup + QA Readability v1

## Active

1. Does prompt/context cleanup reduce backend-shaped wording in first-pass wide-context copy without rebuilding the old phrase cage?
2. Does the writer-facing context now encourage plain food language such as `if protein is still short` instead of internal language such as `approved option` or `gap is still open`?
3. Do terminal-friendly artifacts make QA review faster and less error-prone?
4. Does the product-language scan surface copy problems without becoming a new approval gate?
5. Does `wide_context_practical_coach` remain the best current variant after cleanup?
6. Should the next architecture step be another live GPT-5.5 QA run, or a design pass for promoting only the strongest first-pass architecture ideas into the Daily Coach provider path?

## Known baseline drift

- `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied `718c614` / `42d0bd4` lineage.
- Example mismatch: expected `Read the day before adding more`; actual `Consider the full day`.
- Architecture decision: document this drift and do not patch it inside unrelated wide-context copy/readability work.
- Full-suite green must not be claimed if the drift remains.

## Closed/unchanged boundaries

- Wide-context copy cleanup remains developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, approved context, artifact safety, and future approval decisions.
- Raw provider envelopes are not persisted in default artifacts.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, queue, or production provider promotion is included.
