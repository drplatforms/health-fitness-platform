# Open Questions — Daily Coach Natural Draft + Claim Audit v1

## Active

1. Does a cleaner `ApprovedCoachBrief` let GPT-5.5 produce more natural coaching than the constrained v5 provider path?
2. Does deterministic claim extraction catch the high-risk claims that matter most for v1: food, macro status, serving, timing, training, recovery, causal, addressing, medical/body, and judgment language?
3. Does claim audit reject unsupported claims without over-blocking safe natural wording?
4. Does the single repair attempt remove repairable issues without inventing new facts?
5. Does deterministic fallback trigger after non-repairable findings or failed repair?
6. Are sanitized artifacts useful enough for QA to compare natural draft output against prior constrained provider output?
7. If natural draft improves voice, what is the next runtime QA path before any product/default exposure?

## Closed/unchanged boundaries

- Natural Draft + Claim Audit is developer-only.
- Normal Today behavior is unchanged.
- Existing provider endpoint behavior is unchanged unless explicitly scoped later.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Backend remains final authority for facts, audit, repair limits, fallback, and approval.
- Raw provider output is not written by default.
- No public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation, recovery score changes, worker, scheduler, or queue are included.
