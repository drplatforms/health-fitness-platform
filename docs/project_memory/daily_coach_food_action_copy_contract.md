# Daily Coach Food Action Copy Contract

Milestone: Daily Coach Provider Plainspoken Voice & Action Clarity v5
Status: Backend implementation support contract

## Purpose

Food actions in the Daily Coach card must be specific, plain, and backend-approved.

The provider may explain an approved food suggestion, but it may not invent foods, serving sizes, timing, pairings, meal plans, or macro logic.

## Required food action parts

When available, a food action should include:

1. Friendly food name.
2. Reason the food is suggested.
3. Optional condition tied to the approved gap.

Example:

- Food: canned tuna
- Reason: protein is below target
- Condition: if protein is still short

Preferred output:

> Add canned tuna if you still need more protein.

Rejected output:

> Add one simple option like Tuna, Canned in Water if it fits your meals.

## Friendly food labels

Canonical food names remain traceability/debug data.
Friendly food names are preferred for visible Daily Coach copy.

Example mapping:

- canonical_name: Tuna, Canned in Water
- friendly_name: canned tuna

Visible copy should use “canned tuna” when that friendly label is approved.

Do not leak awkward canonical food labels into visible copy when a friendly label exists.

## Serving display rules

Use serving display only when Backend explicitly approves it.

Do not invent:

- one can
- one packet
- half cup
- one scoop
- one bowl
- one serving
- handful
- plate
- snack size

Use grams-first wording only when suggested grams are approved.

If no serving display is approved, omit serving wording rather than inventing one.

## Food action context

The provider-facing context may include:

- available
- primary_gap
- secondary_gap
- friendly_food_options
- macro_reason
- claim_keys
- preferred_food_sentence_patterns
- banned_food_sentence_patterns

The provider should use this context to write plainly.
It should not expand it into meal planning.

## Preferred patterns

Preferred food sentence patterns:

- add {friendly_name} if you still need more {macro_reason}
- use {friendly_name} if your {macro_reason} gap is still open
- add a simple protein option if protein is still short

## Banned patterns

Banned food sentence patterns:

- if it fits your meals
- if it fits your day
- protein bump
- easy protein bump
- food move
- useful move
- protein-support option
- nutrition support
- support the day
- support the work
- must eat
- need to eat
- required
- fix it by eating

## Grounding requirements

If visible copy says “protein is still short,” quoted_values_used must include the approved protein status claim.

If visible copy says “calories are below target,” quoted_values_used must include the approved calorie status claim.

If visible copy says “canned tuna,” quoted_values_used must include the approved friendly food claim.

If visible copy says a gram amount, quoted_values_used must include the approved suggested gram claim.

## Non-goals

This contract does not add:

- meal planning
- food combinations
- timing recommendations
- serving conversion logic
- provider-created foods
- provider-created portions
- raw food catalog access
