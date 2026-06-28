# Open Questions — Daily Coach Provider Prompt Lab / Voice Lab v1

## Active

1. Which prompt/context variant produces the best plainspoken Daily Coach output across rich, stable, sparse, and missing-domain scenarios?
2. Do fewer examples reduce repeated sentence skeletons?
3. Do fewer broad phrase bans improve naturalness without allowing user-rejected phrases back in?
4. Does food display-language separation prevent canonical labels from leaking into visible copy?
5. Does default no-name addressing improve QA outputs that previously over-addressed Dustin?
6. Is the scoring template enough for QA/Architecture to choose a next provider contract, or does the lab need UX/scoring workflow v2?

## Closed/unchanged boundaries

- Prompt Lab is developer-only.
- Normal Today behavior is unchanged.
- Deterministic remains default.
- OpenAI/direct_ollama remain explicit opt-in/evaluation-only.
- Parser, quote/value validation, display permissions, and deterministic fallback remain mandatory.
- Raw provider output is not written by default.

---

# Open Questions — Daily Coach Provider Plainspoken Voice & Action Clarity v5

## Active

1. Does `gpt-5.5` stop using user-rejected phrasing such as `food move`, `clean work`, `the win is`, `protein bump`, and `if it fits your meals`?
2. Does `food_action_context` cause the provider to name the friendly food, the macro reason, and the backed condition without inventing serving labels, timing, or pairings?
3. Does the provider avoid canonical labels such as `Tuna, Canned in Water` when a friendly label such as `canned tuna` exists?
4. Does the training copy say the actual behavior plainly: prioritize clean reps, keep a couple reps in reserve, and stop before the set turns into a grind?
5. Does recovery wording explain what recovery means today without saying fatigue is irrelevant, performance is guaranteed, or the user is fully recovered?
6. If v5 still misses product voice, should the next milestone become Daily Coach Provider Prompt Lab / Voice Lab v1 instead of another one-off patch?

## Closed/unchanged boundaries

- Provider factual authority is not expanded.
- Parser, quote/value validation, and deterministic fallback remain mandatory.
- Deterministic remains default; OpenAI/direct_ollama remain opt-in/evaluation-only.
- Raw provider output remains local-only diagnostic material.

---

# Open Questions — Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3

## Active

1. Does `gpt-5.5` use `approved_context_brief` as a natural conversation starter without copying framework phrasing?
2. Does `claim_backing_map` improve natural quote-backed phrasing for nutrition status, food suggestions, RIR, readiness, and fatigue risk?
3. Does adaptive verbosity produce richer coaching only when it improves usefulness and actionability?
4. Should v3 hard-fail phrase rules expand beyond the currently obvious bad phrases after QA review?
5. Does the primary user `102` / `2026-06-27` output meet voice naturalness, specificity, usefulness, grounding, and product-readiness targets?

## Closed/unchanged boundaries

- Provider factual authority is not expanded.
- Parser, quote/value validation, and deterministic fallback remain mandatory.
- Deterministic remains default; OpenAI/direct_ollama remain opt-in/evaluation-only.
- Raw provider output remains local-only diagnostic material.

---

# Open Questions — Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

## Active

1. After context enrichment, does `gpt-5.5` consistently use 2-4 high-value approved facts for user `102` / `2026-06-27`?
2. Does the enriched prompt reduce generic Daily Coach copy without causing fact dumps?
3. Do local direct_ollama models understand exact approved claim keys better with the enriched prompt?
4. Should diagnostic quality flags eventually become hard failures, or remain trial-matrix review aids?
5. Which claim metadata fields become most useful for future Prompt Lab/manual scoring work?

## Closed for this milestone

- Deterministic remains default.
- OpenAI/direct_ollama remain opt-in.
- Quote/value validation remains mandatory.
- Raw provider output remains local-only diagnostic material.

---

# Open Questions — Daily Coach Provider Trial Diagnostics v1

## Active

1. After local `.env`/shell loading is confirmed, does OpenAI `gpt-4.1-mini` produce approved Daily Coach value narratives without fallback?
2. Do local direct_ollama models keep misusing `quoted_values_used` after prompt/diagnostic review?
3. Which local diagnostic mode is most useful for QA: terminal inspection, local raw-output files outside repo, or both?
4. Which Ollama cleanup option is most reliable on the Windows Ollama host: explicit unload, keep_alive `0`, or both?
5. Should deeper OpenAI response classification eventually move into provider runtime service code if other provider endpoints need it?

## Closed for this milestone

- Deterministic remains default.
- direct_ollama/openai remain opt-in.
- Trial diagnostics must not change normal product runtime behavior.
- Automated tests must not call live providers.

---

## Daily Coach Provider Context Selection & Coaching Synthesis v2 open QA questions

- Does gpt-5.5 use today_story and high-value claims to become more specific without becoming report-like?
- Does adaptive verbosity improve priority_action usefulness without metric repetition?
- Does food suggestion usage improve actionability when approved and quote-valid?
- Do field-specific claim budgets correctly flag too-few/too-many claim usage without weakening hard safety validation?


---

# Open Questions — Daily Coach Provider Human Voice & Food Action Specificity v4

## Active

1. Does gpt-5.5 use friendly food labels such as `canned tuna` instead of raw canonical names such as `Tuna, Canned in Water`?
2. Does the provider avoid invented serving units such as cans, scoops, cups, bowls, or handfuls unless Backend approves them?
3. Does `nutrition_action_context` make the priority action more concrete without turning the card into meal planning?
4. Do the new phrase failures eliminate `make nutrition support the work`, `useful move`, `support the day`, and `fatigue does not require backing off today`?
5. Does the output sound like a human coach talking to Dustin while keeping grounding at 5?

## Closed/unchanged boundaries

- Provider factual authority is not expanded.
- Parser, quote/value validation, and deterministic fallback remain mandatory.
- Deterministic remains default; OpenAI/direct_ollama remain opt-in/evaluation-only.
- Raw provider output remains local-only diagnostic material.
