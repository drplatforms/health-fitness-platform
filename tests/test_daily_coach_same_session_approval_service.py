from __future__ import annotations

from services.daily_coach_same_session_approval_service import (
    DailyCoachSameSessionApprovalError,
    apply_approved_preview_to_today_card,
    build_same_session_approval_from_preview,
    validate_preview_for_same_session_approval,
    validate_same_session_approval,
)


def _preview(**overrides):
    payload = {
        "user_id": 102,
        "date": "2026-06-20",
        "next_action_id": "log_food",
        "next_action_title": "Log a meal or snack",
        "workflow_target": "nutrition_quick_log",
        "provider_enabled": True,
        "provider_attempted": True,
        "selected_provider": "direct_ollama",
        "selected_model": "qwen3:32b",
        "parse_success": True,
        "validation_success": True,
        "fallback_used": False,
        "fallback_reason": None,
        "approved_narrative": {
            "coach_note": "Start with your next meal log today, then use that signal to keep the rest of the day focused.",
            "key_takeaway": "Log the next meal first.",
            "recommended_focus": "nutrition logging",
            "confidence_language": "This stays tied to approved context.",
            "used_approved_facts": ["Daily Next Action: Log a meal or snack"],
            "avoided_claims": [],
        },
        "deterministic_fallback_note": "Log your next meal or snack.",
        "approved_focus": "nutrition logging",
        "context_summary": {},
        "latency_ms": 1000,
    }
    payload.update(overrides)
    return payload


def _today_card():
    return {
        "date": "2026-06-20",
        "card_title": "Today’s Coach Note",
        "coach_note": "Your best move today is to close the logging gap first.",
        "next_action_title": "Log a meal or snack",
        "cta_label": "Next action: Log a meal or snack",
        "cta_target": "nutrition_quick_log",
        "supporting_reason": "Add today's food intake.",
    }


def test_valid_preview_can_build_same_session_approval():
    preview = _preview()

    eligibility = validate_preview_for_same_session_approval(
        preview,
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )
    approval = build_same_session_approval_from_preview(
        preview,
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
        approved_at="2026-06-20T12:00:00+00:00",
    )

    assert eligibility.eligible is True
    assert approval.is_session_only is True
    assert approval.is_provider_generated is True
    assert approval.approved_narrative == preview["approved_narrative"]["coach_note"]
    assert approval.developer_metadata["persisted"] is False


def test_rejected_preview_cannot_be_approved_or_displayed():
    preview = _preview(
        validation_success=False,
        fallback_used=True,
        fallback_reason="provider_validation_failed",
        approved_narrative=None,
    )

    eligibility = validate_preview_for_same_session_approval(
        preview,
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )

    assert eligibility.eligible is False
    assert eligibility.reason == "fallback_used"
    try:
        build_same_session_approval_from_preview(
            preview,
            user_id=102,
            target_date="2026-06-20",
            next_action_id="log_food",
            workflow_target="nutrition_quick_log",
        )
    except DailyCoachSameSessionApprovalError:
        pass
    else:
        raise AssertionError("Rejected preview should not be approvable.")


def test_approval_requires_parse_and_validation_success():
    for overrides, expected_reason in [
        ({"parse_success": False}, "parse_failed"),
        ({"validation_success": False}, "validation_failed"),
    ]:
        eligibility = validate_preview_for_same_session_approval(
            _preview(**overrides),
            user_id=102,
            target_date="2026-06-20",
            next_action_id="log_food",
            workflow_target="nutrition_quick_log",
        )
        assert eligibility.eligible is False
        assert eligibility.reason == expected_reason


def test_provider_debug_leak_text_blocks_approval():
    preview = _preview(
        approved_narrative={
            "coach_note": "qwen model raw_response prompt should never appear",
        }
    )

    eligibility = validate_preview_for_same_session_approval(
        preview,
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )

    assert eligibility.eligible is False
    assert eligibility.reason == "display_validation_failed"


def test_same_session_approval_replaces_note_but_preserves_cta_and_action_facts():
    preview = _preview()
    approval = build_same_session_approval_from_preview(
        preview,
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )

    card = apply_approved_preview_to_today_card(
        _today_card(),
        approval,
        user_id=102,
        next_action_id="log_food",
    )

    assert card["coach_note"] == preview["approved_narrative"]["coach_note"]
    assert card["cta_label"] == "Next action: Log a meal or snack"
    assert card["cta_target"] == "nutrition_quick_log"
    assert "selected_model" not in card
    assert "provider" not in str(card).lower()


def test_context_mismatch_ignores_or_rejects_approval():
    approval = build_same_session_approval_from_preview(
        _preview(),
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )

    eligibility = validate_same_session_approval(
        approval,
        user_id=103,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )
    unchanged = apply_approved_preview_to_today_card(
        _today_card(),
        approval,
        user_id=103,
        next_action_id="log_food",
    )

    assert eligibility.eligible is False
    assert unchanged == _today_card()


def test_approval_is_session_only_and_has_no_persistence_payload():
    approval = build_same_session_approval_from_preview(
        _preview(),
        user_id=102,
        target_date="2026-06-20",
        next_action_id="log_food",
        workflow_target="nutrition_quick_log",
    )
    payload = approval.to_dict()

    assert payload["is_session_only"] is True
    assert payload["developer_metadata"]["persisted"] is False
    assert "database" not in str(payload).lower()
    assert "report_persistence" not in str(payload).lower()
