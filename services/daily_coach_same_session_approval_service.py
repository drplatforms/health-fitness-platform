from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

SAME_SESSION_APPROVED_PROVIDER_PREVIEW_SOURCE = "same_session_approved_provider_preview"
DAILY_COACH_SAME_SESSION_MAX_NOTE_CHARACTERS = 700

_NO_LEAK_FORBIDDEN_TERMS = {
    "provider",
    "model",
    "qwen",
    "ollama",
    "direct_ollama",
    "raw_response",
    "prompt",
    "json",
    "fallback_reason",
    "parse_success",
    "validation_success",
    "traceback",
    "stack trace",
    "validation error",
    "as an ai language model",
}

_UNSUPPORTED_CLAIM_TERMS = {
    "calorie target",
    "protein target",
    "diagnose",
    "diagnosis",
    "treat",
    "treatment",
    "rehab",
    "injury",
    "fatigue is",
    "you recovered",
    "adherence trend",
    "completed your workout",
    "guarantee",
    "guaranteed",
}


@dataclass(frozen=True)
class DailyCoachSameSessionApprovalEligibility:
    eligible: bool
    reason: str
    user_safe_reason: str
    developer_reason: str
    parse_success: bool
    validation_success: bool
    approved_narrative_returned: bool
    no_leak_validation_success: bool
    same_user: bool
    same_date: bool
    same_next_action: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachSameSessionApproval:
    user_id: int
    date: str
    next_action_id: str
    next_action_title: str
    workflow_target: str
    approved_narrative: str
    approved_at: str
    source: str = SAME_SESSION_APPROVED_PROVIDER_PREVIEW_SOURCE
    is_provider_generated: bool = True
    is_session_only: bool = True
    developer_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DailyCoachSameSessionApprovalError(ValueError):
    """Raised when a same-session approval is not eligible for display."""


def build_same_session_approval_from_preview(
    preview: dict[str, Any],
    *,
    user_id: int,
    target_date: str,
    next_action_id: str,
    workflow_target: str | None = None,
    approved_at: str | None = None,
) -> DailyCoachSameSessionApproval:
    """Build a session-only approval from an already validated preview payload.

    This function never calls a provider and never persists anything. It only
    converts an existing public-safe preview into a small display approval after
    checking parse, validation, context, and no-leak rules.
    """

    eligibility = validate_preview_for_same_session_approval(
        preview,
        user_id=user_id,
        target_date=target_date,
        next_action_id=next_action_id,
        workflow_target=workflow_target,
    )
    if not eligibility.eligible:
        raise DailyCoachSameSessionApprovalError(eligibility.developer_reason)

    narrative = _preview_narrative_text(preview)
    return DailyCoachSameSessionApproval(
        user_id=user_id,
        date=str(target_date),
        next_action_id=str(preview.get("next_action_id") or next_action_id),
        next_action_title=str(preview.get("next_action_title") or "Next action"),
        workflow_target=str(
            preview.get("workflow_target") or workflow_target or "today"
        ),
        approved_narrative=narrative,
        approved_at=approved_at or datetime.now(UTC).isoformat(),
        developer_metadata={
            "approval_source": SAME_SESSION_APPROVED_PROVIDER_PREVIEW_SOURCE,
            "provider_label": preview.get("selected_provider"),
            "model_label": preview.get("selected_model"),
            "fallback_used": bool(preview.get("fallback_used")),
            "latency_ms": preview.get("latency_ms"),
            "is_session_only": True,
            "persisted": False,
        },
    )


def validate_preview_for_same_session_approval(
    preview: dict[str, Any] | None,
    *,
    user_id: int,
    target_date: str,
    next_action_id: str,
    workflow_target: str | None = None,
) -> DailyCoachSameSessionApprovalEligibility:
    preview = preview or {}
    parse_success = bool(preview.get("parse_success"))
    validation_success = bool(preview.get("validation_success"))
    approved_narrative_returned = bool(_preview_narrative_text(preview))
    no_leak_validation_success = _text_passes_no_leak_validation(
        _preview_narrative_text(preview)
    )
    same_user = int(preview.get("user_id") or -1) == int(user_id)
    same_date = str(preview.get("date") or "") == str(target_date)
    same_next_action = str(preview.get("next_action_id") or "") == str(next_action_id)
    same_workflow = True
    if workflow_target is not None:
        same_workflow = str(preview.get("workflow_target") or "") == str(
            workflow_target
        )

    if preview.get("fallback_used"):
        return _eligibility(
            False,
            "fallback_used",
            "The preview fell back to the deterministic note.",
            "Fallback preview cannot be approved for same-session display.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )
    if not parse_success:
        return _eligibility(
            False,
            "parse_failed",
            "The preview did not pass parsing.",
            "Same-session approval requires parse_success true.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )
    if not validation_success:
        return _eligibility(
            False,
            "validation_failed",
            "The preview did not pass validation.",
            "Same-session approval requires validation_success true.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )
    if not approved_narrative_returned:
        return _eligibility(
            False,
            "missing_approved_narrative",
            "The preview did not return approved coach text.",
            "Preview approved_narrative.coach_note is missing.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )
    if not no_leak_validation_success:
        return _eligibility(
            False,
            "display_validation_failed",
            "The approved text is not safe for normal display.",
            "Approved narrative contains provider/debug/unsupported claim terms.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )
    if not (same_user and same_date and same_next_action and same_workflow):
        return _eligibility(
            False,
            "context_mismatch",
            "The approved preview is for a different Today context.",
            "Same-session approval user/date/action/workflow mismatch.",
            parse_success,
            validation_success,
            approved_narrative_returned,
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action and same_workflow,
        )

    return _eligibility(
        True,
        "eligible",
        "Preview is eligible for this session.",
        "Preview passed parse, validation, no-leak, and context checks.",
        parse_success,
        validation_success,
        approved_narrative_returned,
        no_leak_validation_success,
        same_user,
        same_date,
        True,
    )


def validate_same_session_approval(
    approval: DailyCoachSameSessionApproval | dict[str, Any] | None,
    *,
    user_id: int,
    target_date: str,
    next_action_id: str | None = None,
    workflow_target: str | None = None,
) -> DailyCoachSameSessionApprovalEligibility:
    payload = (
        approval.to_dict()
        if isinstance(approval, DailyCoachSameSessionApproval)
        else approval or {}
    )
    narrative = str(payload.get("approved_narrative") or "").strip()
    no_leak_validation_success = _text_passes_no_leak_validation(narrative)
    same_user = int(payload.get("user_id") or -1) == int(user_id)
    same_date = str(payload.get("date") or "") == str(target_date)
    same_next_action = True
    if next_action_id is not None:
        same_next_action = str(payload.get("next_action_id") or "") == str(
            next_action_id
        )
    if workflow_target is not None:
        same_next_action = same_next_action and str(
            payload.get("workflow_target") or ""
        ) == str(workflow_target)
    session_only = bool(payload.get("is_session_only"))
    source_ok = payload.get("source") == SAME_SESSION_APPROVED_PROVIDER_PREVIEW_SOURCE

    if not (
        narrative
        and no_leak_validation_success
        and same_user
        and same_date
        and same_next_action
        and session_only
        and source_ok
    ):
        return _eligibility(
            False,
            "approval_invalid",
            "The approved preview is no longer valid for this Today context.",
            "Approval failed context/session/no-leak/source validation.",
            True,
            True,
            bool(narrative),
            no_leak_validation_success,
            same_user,
            same_date,
            same_next_action,
        )

    return _eligibility(
        True,
        "eligible",
        "Approved preview is valid for this session.",
        "Approval is same-session, same-context, and display-safe.",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    )


def apply_approved_preview_to_today_card(
    today_card: dict[str, Any],
    approval: DailyCoachSameSessionApproval | dict[str, Any] | None,
    *,
    user_id: int,
    next_action_id: str | None = None,
) -> dict[str, Any]:
    """Return a public Today card with only coach_note replaced when valid."""

    card = dict(today_card or {})
    target_date = str(card.get("date") or "")
    workflow_target = str(card.get("cta_target") or "") or None
    eligibility = validate_same_session_approval(
        approval,
        user_id=user_id,
        target_date=target_date,
        next_action_id=next_action_id,
        workflow_target=workflow_target,
    )
    if not eligibility.eligible:
        return card

    payload = (
        approval.to_dict()
        if isinstance(approval, DailyCoachSameSessionApproval)
        else approval or {}
    )
    card["coach_note"] = str(payload.get("approved_narrative") or "").strip()
    return card


def _preview_narrative_text(preview: dict[str, Any]) -> str:
    narrative = preview.get("approved_narrative")
    if not isinstance(narrative, dict):
        return ""
    return str(narrative.get("coach_note") or "").strip()


def _text_passes_no_leak_validation(text: str) -> bool:
    normalized = " ".join(str(text or "").lower().split())
    if not normalized:
        return False
    if len(normalized) > DAILY_COACH_SAME_SESSION_MAX_NOTE_CHARACTERS:
        return False
    return not any(
        term in normalized
        for term in _NO_LEAK_FORBIDDEN_TERMS | _UNSUPPORTED_CLAIM_TERMS
    )


def _eligibility(
    eligible: bool,
    reason: str,
    user_safe_reason: str,
    developer_reason: str,
    parse_success: bool,
    validation_success: bool,
    approved_narrative_returned: bool,
    no_leak_validation_success: bool,
    same_user: bool,
    same_date: bool,
    same_next_action: bool,
) -> DailyCoachSameSessionApprovalEligibility:
    return DailyCoachSameSessionApprovalEligibility(
        eligible=eligible,
        reason=reason,
        user_safe_reason=user_safe_reason,
        developer_reason=developer_reason,
        parse_success=parse_success,
        validation_success=validation_success,
        approved_narrative_returned=approved_narrative_returned,
        no_leak_validation_success=no_leak_validation_success,
        same_user=same_user,
        same_date=same_date,
        same_next_action=same_next_action,
    )
