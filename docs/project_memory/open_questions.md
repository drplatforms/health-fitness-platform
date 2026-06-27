# Open Questions — Daily Coach Narrative Provider Trial Matrix v1

Current milestone: Daily Coach Narrative Provider Trial Matrix v1.

Open questions for Architecture / Agent Engineering after trial data exists:

1. Is OpenAI materially better than local direct_ollama for Daily Coach synthesis?
2. Does direct_ollama remain useful as offline developer mode?
3. Which provider best follows the strict schema and approved value quote contract?
4. Which provider falls back least often?
5. Which provider produces the most useful coaching copy across recovery, training, and nutrition contexts?
6. Does any provider repeatedly trigger quote/value validation failures?
7. Should deterministic remain default? Expected answer: yes.
8. Should any provider become default now? Expected answer: no.

No provider default change is authorized by this milestone.

# Open Questions — Daily Coach Narrative Approved Value Quote Validation v1

Current milestone: Daily Coach Narrative Approved Value Quote Validation v1.

Status: authorized for backend implementation.

## Current Architecture question

Should Architecture accept an explicit approved value registry plus quote/value validator as the safety fence for value-aware Daily Coach provider narratives?

Requested final status:

`DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED`.

## Resolved direction from handoff

1. AI may quote deterministic backend values only when those values are approved, public-safe, present in provider context, and validated before rendering.
2. `quoted_values_used` must declare every quoted value.
3. Narrative prose must also be scanned for undeclared value claims.
4. Unknown, display-blocked, or invented quoted values cause deterministic fallback.
5. Deterministic remains default; providers remain opt-in.
6. Normal endpoint remains public-safe and hides runtime/validation internals.
7. Debug endpoint may expose sanitized validation metadata.

## Future questions preserved

1. Should approved quote validation be generalized across weekly coach summaries and report sections?
2. Should value claims eventually use a shared platform-wide claim registry?
3. Should Daily Coach Developer Mode render quote validation details?
4. Should OpenAI/direct_ollama runtime QA happen after this validation fence is accepted?
5. Should provider output persistence wait until quote validation is proven through QA?

## Current answer boundary

This milestone adds backend quote/value validation only.

It does not authorize normal Streamlit display, persistence, provider default changes, report integration, meal planning, RAG, or multi-agent orchestration.


## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- qwen3:32b is research / future premium async candidate only
- deterministic fallback remains mandatory
- backend owns truth
- AI explains backend-approved truth
