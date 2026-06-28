# Daily Coach Plainspoken Voice Contract

Milestone: Daily Coach Provider Plainspoken Voice & Action Clarity v5
Status: Backend implementation support contract

## Purpose

The Daily Coach card should sound like a practical coach talking to Dustin.
It should say the actual action, explain why it matters, and avoid turning simple advice into slogans or backend-shaped phrases.

This contract applies to provider-written visible Daily Coach fields:

- headline
- summary
- nutrition_note
- training_note
- recovery_note
- priority_action

It does not expand provider factual authority.
Backend-approved claims, quote/value validation, parser validation, and deterministic fallback remain the safety boundary.

## Voice target

The Daily Coach should be:

- plainspoken
- direct
- useful
- specific
- calm
- grounded
- short enough to scan

The Daily Coach should not sound like:

- a motivational poster
- product marketing
- a backend system
- a validator
- a report generator
- a wellness influencer
- a medical disclaimer

## Core product questions

A good Daily Coach card answers:

1. Can I train today?
2. How should I train?
3. What nutrition issue matters?
4. What exact food action should I take, if any?
5. What should I avoid overdoing?

## Plainspoken rules

Prefer:

- “You can train as planned today.”
- “Keep a couple reps in reserve.”
- “Stop before the set turns into a grind.”
- “Calories and protein are both below target.”
- “Add canned tuna if you still need more protein.”
- “You do not need to overhaul the whole day.”

Avoid:

- “food move”
- “clean work”
- “make clean reps the win”
- “the win is”
- “useful move”
- “main lever”
- “support the work”
- “support the day”
- “nutrition support”
- “effort anchor”
- “planned effort range”
- “bigger nutrition overhaul”
- “rebuilding the whole plan”
- “if it fits your meals”
- “if it fits your day”
- “protein bump”
- “easy protein bump”
- “fatigue does not require backing off today”
- “Tuna, Canned in Water” when a friendly label exists

## Training language

Training advice should say the actual behavior.

Allowed direction:

- Prioritize clean reps.
- Keep a couple reps in reserve.
- Stop before the set turns into a grind.
- Train as planned; do not turn it into a max-effort test.
- Do the planned session without chasing extra intensity.

Avoid:

- make clean reps the win
- the win is
- effort anchor
- planned effort range
- controlled execution framework
- clean work

## Recovery language

Recovery language should explain what recovery means today.

Allowed direction:

- Recovery looks good enough to train as planned.
- You do not need to back off today.
- That gives you room to do the work, not a reason to turn it into a max-effort test.
- Train normally, not recklessly.

Avoid:

- fatigue does not require backing off today
- recovery guarantees performance
- you are fully recovered
- fatigue is not a concern at all

## Nutrition language

Nutrition advice should name the gap and the action.

Allowed direction:

- Calories and protein are both below target.
- Protein is still short.
- Add canned tuna if you still need more protein.
- Use a simple protein option if the gap is still open.
- Do not try to fix the whole day at once.

Avoid:

- make nutrition support the work
- nutrition support
- support the day
- support the work
- useful move
- food move
- if it fits your meals
- protein bump
- easy protein bump
- rebuilding the whole plan

## Grounding rules

Every concrete food, value, status, amount, range, readiness claim, fatigue claim, or macro-gap claim must be backed by approved claim keys and quoted in provider output.

The provider must not invent:

- foods
- servings
- pairings
- timing
- meal plans
- macro logic
- recovery explanations
- training changes

## Acceptance target

Provider output should score at least 4 out of 5 for:

- plainspoken voice
- action clarity
- food specificity
- training clarity
- recovery implication
- product readiness

Grounding must remain 5 out of 5.
