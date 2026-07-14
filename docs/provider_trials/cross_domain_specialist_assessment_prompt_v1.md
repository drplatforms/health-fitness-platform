# Cross-Domain Specialist Assessment Prompt v1

Prepare a developer-only candidate assessment from the bounded semantic
context. Treat its evidence IDs, fact keys, typed values, action IDs, action
types, parameters, and condition codes as the complete source of truth.

Return one JSON object only. Do not use Markdown, prose before or after the
JSON, or any keys outside the required response shape.

Assess recovery, nutrition, and training separately. Observations may describe
the supplied semantic evidence, but they do not create facts, actions, food
choices, servings, timing, calories, macros, workout changes, or medical
conclusions. Select only listed action keys. A domain may select or veto only
actions listed for that domain. Cite only evidence IDs listed for the
applicable domain. Do not change the workout, nutrition targets, or user state.

Do not infer missing facts from metadata, source systems, IDs, or unlisted
history. Condition codes describe limits and gaps; they are not selectable
actions and must not be rewritten as new facts.

Supporting claims provide factual support for their listed action only. Do not
use them to claim that trend or data-quality limits are resolved.

Use cross-domain tensions only when the cited evidence actually creates a
meaningful tradeoff. Keep the assessment concise and evidence-grounded.
