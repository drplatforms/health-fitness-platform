# Daily Coach Narrative Context v1 Design

Status: PROPOSED / PLANNING ONLY

Related milestone: `Daily Coach Narrative v1 Planning`

## Design intent

`DailyCoachNarrativeContext` is the proposed backend-approved context packet for a future short coach-style narrative under the deterministic Daily Next Action Panel.

It exists to give a model enough approved context to explain the backend-selected action without letting the model choose actions, invent facts, override confidence, or bypass validators.

## Proposed pipeline

```text
Daily Next Action state
→ DailyCoachNarrativeContext
→ CandidateDailyCoachNarrative JSON attempt
→ narrative parser
→ narrative validator
→ ApprovedDailyCoachNarrative or deterministic fallback
→ future Developer Mode preview
→ future normal Today UI only after acceptance
```

Planning v1 stops at the design boundary. No runtime implementation is added yet.

## Proposed context fields

| Field | Type | Source owner | Notes |
|---|---|---|---|
| `user_id` | int | Backend | Existing selected user. |
| `date` | string | Backend | ISO date for the daily context. |
| `next_action_id` | string | Daily Next Action service | Backend-selected action id. |
| `next_action_title` | string | Daily Next Action service | Deterministic title shown to user. |
| `next_action_reason` | string | Daily Next Action service | Backend-owned reason. |
| `workflow_target` | string | Daily Next Action service | Existing workflow target only. |
| `severity` | string | Backend | Optional severity/priority label if available. |
| `priority` | int/string | Backend | Optional priority if already available. |
| `approved_focus` | string | Backend | Exact required `recommended_focus` value. |
| `approved_facts` | list[str] | Backend | Exact strings the provider may cite. |
| `approved_limitations` | list[str] | Backend | Confidence/data limitations. |
| `nutrition_status_summary` | string/null | Backend | Compact approved summary only. |
| `recovery_status_summary` | string/null | Backend | Compact approved summary only. |
| `workout_status_summary` | string/null | Backend | Compact approved summary only. |
| `forbidden_claims` | list[str] | Backend | Explicit disallowed claims/fragments. |
| `confidence_language` | string | Backend | Provider must not exceed this. |

## Excluded inputs

Do not include:

- raw nutrition logs
- raw workout logs
- raw recovery check-ins
- raw provider output
- raw debug payloads
- full catalog dumps
- unfiltered history
- raw SQL rows
- raw source food payloads
- raw actual-set notes
- runtime metadata
- validator internals
- private diagnostics

## Proposed candidate output object

```json
{
  "coach_note": "string",
  "key_takeaway": "string",
  "recommended_focus": "string",
  "confidence_language": "string",
  "used_approved_facts": ["string"],
  "avoided_claims": ["string"]
}
```

The output shape intentionally matches the tightened coach voice bakeoff contract unless future implementation discovers a reason to specialize it.

## Validation stages

Future validation should proceed in this order:

1. Parse strict JSON object.
2. Reject markdown/prose wrappers.
3. Reject missing keys.
4. Reject extra keys.
5. Require exact `recommended_focus` match.
6. Require every `used_approved_facts` item to exactly match `approved_facts`.
7. Reject changed action or changed workflow target.
8. Reject invented numbers, foods, exercises, targets, workouts, or serving sizes.
9. Reject unsupported fatigue, recovery, readiness, progression, or consistency claims.
10. Reject medical or clinical nutrition claims.
11. Reject meal plans and unapproved food/exercise suggestions.
12. Enforce compact coach-note length.
13. Approve or fall back deterministically.

## Deterministic fallback

Fallback output should use the existing Daily Next Action card text:

- deterministic title
- deterministic backend reason
- deterministic workflow target

Rejected provider output must not appear in normal UI.

## Future model strategy

The first runtime QA should compare:

- `qwen3:8b` as practical candidate
- `qwen2.5:3b` as compliant small baseline
- `qwen3:32b` as offline quality reference

`qwen3:14b` and `qwen3:30b-a3b` are not recommended for v1 runtime until they show stronger contract adherence.

## Implementation sequence

Recommended implementation sequence after planning acceptance:

1. `Daily Coach Narrative Context Builder v1`
2. Offline narrative runtime QA over fixed context fixtures
3. Provider wrapper behind explicit opt-in flag
4. Streamlit Developer Mode preview only
5. Normal Today UI integration only after runtime QA and Architecture acceptance

## Non-goals

This design does not approve:

- model promotion
- qwen3 production use
- Today integration
- Streamlit integration
- report integration
- direct_ollama default change
- validator loosening
- provider gate changes
- RAG, embeddings, scraping, agents, meal planning, or AI-generated food/exercise suggestions
