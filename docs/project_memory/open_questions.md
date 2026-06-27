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
