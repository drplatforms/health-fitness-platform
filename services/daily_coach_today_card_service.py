from __future__ import annotations

from datetime import date

from models.daily_coach_narrative_models import (
    DAILY_COACH_TODAY_CARD_DISPLAY_SOURCE,
    DailyCoachTodayCard,
)
from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DailyNextAction,
)
from services.daily_next_action_service import build_daily_next_action

DAILY_COACH_TODAY_CARD_TITLE = "Today’s Coach Note"
DAILY_COACH_TODAY_CARD_MAX_NOTE_CHARACTERS = 520

_NORMAL_UI_FORBIDDEN_TERMS = {
    "provider",
    "model",
    "qwen",
    "ollama",
    "direct_ollama",
    "fallback_reason",
    "parse_success",
    "validation_success",
    "raw_response",
    "prompt",
    "stack trace",
    "traceback",
    "json",
}

_UNSAFE_CLAIM_TERMS = {
    "diagnose",
    "diagnosis",
    "treat",
    "treatment",
    "rehab",
    "injury",
    "doctor",
    "physical therapy",
    "guarantee",
    "guaranteed",
    "safe for everyone",
}


class DailyCoachTodayCardValidationError(ValueError):
    """Raised when the deterministic Today card violates public display rules."""


def build_daily_coach_today_card(
    user_id: int,
    *,
    target_date: str | None = None,
    action: DailyNextAction | None = None,
) -> DailyCoachTodayCard:
    """Build the deterministic, public-safe Today Coach Note card.

    This service is downstream of Daily Next Action. It never calls provider
    generation, never reads raw provider output, never persists narrative text,
    and never changes Daily Next Action selection.
    """

    card_date = target_date or date.today().isoformat()
    selected_action = action or build_daily_next_action(
        user_id,
        target_date=card_date,
    )

    card = DailyCoachTodayCard(
        user_id=user_id,
        date=card_date,
        next_action_id=selected_action.action_id,
        next_action_title=selected_action.title,
        workflow_target=selected_action.workflow_target,
        card_title=DAILY_COACH_TODAY_CARD_TITLE,
        coach_note=_coach_note_for_action(selected_action),
        cta_label=f"Next action: {selected_action.title}",
        cta_target=selected_action.workflow_target,
        supporting_reason=_supporting_reason(selected_action),
        display_source=DAILY_COACH_TODAY_CARD_DISPLAY_SOURCE,
        is_provider_generated=False,
        is_fallback=False,
        user_visible=True,
        developer_metadata={
            "source_service": "daily_coach_today_card_service",
            "daily_next_action_primary": True,
            "normal_today_load_calls_provider": False,
            "narrative_persisted": False,
        },
    )

    violations = validate_daily_coach_today_card(card)
    if violations:
        raise DailyCoachTodayCardValidationError("; ".join(violations))

    return card


def validate_daily_coach_today_card(card: DailyCoachTodayCard) -> list[str]:
    violations: list[str] = []

    required_public_text = [
        card.date,
        card.next_action_title,
        card.workflow_target,
        card.card_title,
        card.coach_note,
        card.cta_label,
        card.cta_target,
        card.supporting_reason,
    ]
    if any(not str(value).strip() for value in required_public_text):
        violations.append("DailyCoachTodayCard public fields must be non-empty.")

    if card.display_source != DAILY_COACH_TODAY_CARD_DISPLAY_SOURCE:
        violations.append(
            "DailyCoachTodayCard display source must remain deterministic."
        )

    if card.is_provider_generated:
        violations.append("DailyCoachTodayCard must not be provider-generated in v1.")

    if not card.user_visible:
        violations.append("DailyCoachTodayCard must be user-visible when returned.")

    if len(card.coach_note) > DAILY_COACH_TODAY_CARD_MAX_NOTE_CHARACTERS:
        violations.append("DailyCoachTodayCard coach note is too long.")

    normal_text = " ".join(
        [
            card.card_title,
            card.coach_note,
            card.next_action_title,
            card.cta_label,
            card.cta_target,
            card.supporting_reason,
        ]
    ).lower()

    for term in _NORMAL_UI_FORBIDDEN_TERMS:
        if term in normal_text:
            violations.append(
                "DailyCoachTodayCard public text exposes provider/debug terminology."
            )
            break

    for term in _UNSAFE_CLAIM_TERMS:
        if term in normal_text:
            violations.append(
                "DailyCoachTodayCard public text includes unsafe medical/claim language."
            )
            break

    if "calories" in normal_text or "protein" in normal_text:
        violations.append(
            "DailyCoachTodayCard public text must not invent calorie/protein targets."
        )

    return violations


def _coach_note_for_action(action: DailyNextAction) -> str:
    if action.action_id == DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN:
        return (
            "Keep this simple today: start by updating your recovery check-in. "
            "Once sleep, energy, soreness, and body weight are current, the rest "
            "of today’s plan has a cleaner base."
        )

    if action.action_id == DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE:
        return (
            "Your best move today is to keep training controlled. Start with the "
            "conservative training action above, then let the rest of the day stay "
            "simple instead of forcing extra intensity."
        )

    if action.action_id == DAILY_NEXT_ACTION_LOG_FOOD:
        return (
            "Your best move today is to close the logging gap first. Log your "
            "next meal or snack so the coach has enough nutrition signal to make "
            "the rest of today’s guidance more useful."
        )

    if action.action_id == DAILY_NEXT_ACTION_REVIEW_WORKOUT:
        return (
            "Today is a good day to review the approved workout before you start. "
            "Check the plan first so the session stays tied to the current training "
            "and recovery context."
        )

    if action.action_id == DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE:
        return (
            "Use the report guidance as today’s anchor. Start there before making "
            "bigger changes so the next step stays tied to validated report context."
        )

    if action.action_id == DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS:
        return (
            "Keep the nutrition read grounded today. Review the target-vs-actual "
            "view first so you can see what the app can safely show before changing "
            "the plan."
        )

    return (
        "Today’s plan is still available. Start with the next action above and "
        "keep the day focused on one clear step."
    )


def _supporting_reason(action: DailyNextAction) -> str:
    return action.summary.strip() or action.reason.strip()
