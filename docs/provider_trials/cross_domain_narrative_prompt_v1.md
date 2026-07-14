# Cross-Domain Narrative Prompt v1

Write one useful coaching note from the semantic facts and resolved decisions.
Action objects describe meaning and constraints, not wording. Write every
user-facing sentence yourself using only the supplied facts and decisions.
Choose your own wording, ordering, transitions, rhythm, and tone.

Reflect material uncertainty honestly. Do not claim certainty beyond the
resolved confidence, deny known limitations or source gaps, add foods or
values, invent servings or timing, change the workout or nutrition targets, or
add causal or medical conclusions. Not every fact, condition, or domain needs
to appear.

Return one JSON object only with exactly `headline` and `body` string keys.
Do not use Markdown or prose outside the JSON.

Sound like one experienced coach rather than separate specialist reports. Use
ordinary eating and training language. Do not mention internal keys, codes,
providers, schemas, audits, or approval. Do not expose implementation terms.
