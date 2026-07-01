from __future__ import annotations

from pathlib import Path

import pytest

from models.daily_coach_recovery_copy_models import RecoveryAwareCoachCopyContract
from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
    DailyNextAction,
)
from services.daily_coach_today_card_service import (
    DAILY_COACH_TODAY_CARD_MAX_NOTE_CHARACTERS,
    build_daily_coach_today_card,
    validate_daily_coach_today_card,
)

PUBLIC_FORBIDDEN_TERMS = [
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
    "contract_version",
    "reason_codes",
    "source_services",
    "data_quality_status",
    "recovery_aware_coach_copy_contract",
]

UNSAFE_PUBLIC_COPY_TERMS = [
    "diagnose",
    "diagnosis",
    "medical",
    "injury",
    "illness",
    "overtraining",
    "must deload",
    "forced deload",
    "automatic deload",
    "automatic progression",
    "should not train",
    "unsafe to train",
]

RECOVERY_MATRIX_STATES = [
    "none",
    "unavailable",
    "limited",
    "usable_low_pressure",
    "usable_moderate_pressure",
    "usable_high_pressure",
]


@pytest.fixture(autouse=True)
def _normal_today_card_never_calls_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    def provider_should_not_run(*args, **kwargs):
        raise AssertionError("Daily Coach Note copy matrix must not call providers.")

    monkeypatch.setattr(
        "services.daily_coach_narrative_provider_service.call_ollama_generate",
        provider_should_not_run,
    )


def _approved_actions() -> list[DailyNextAction]:
    return [
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
            title="Complete recovery check-in",
            summary="Update sleep, energy, soreness, and body weight first.",
            reason="Recovery context is limited until the check-in is current.",
            priority=1,
            workflow_target="today_recovery_checkin",
            severity="info",
            evidence={"scenario": "data_quality_limited"},
        ),
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
            title="Keep training conservative",
            summary="Use a controlled training stance before pushing intensity.",
            reason="Current recovery context supports a controlled training day.",
            priority=2,
            workflow_target="today_recovery_aware_workout",
            severity="warning",
            evidence={"scenario": "recovery_limited"},
        ),
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_LOG_FOOD,
            title="Log a meal or snack",
            summary="Add today's food intake so nutrition guidance has enough data.",
            reason="Nutrition context is limited until more food data is logged.",
            priority=3,
            workflow_target="nutrition_quick_log",
            severity="info",
            evidence={"scenario": "nutrition_training_mismatch"},
        ),
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_REVIEW_WORKOUT,
            title="Review today's workout",
            summary="Check the approved workout before starting or logging sets.",
            reason="The current plan is ready for review before execution.",
            priority=4,
            workflow_target="workout_preview",
            severity="success",
            evidence={"scenario": "aligned_managed"},
        ),
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
            title="Review today's report guidance",
            summary="Use validated report sections to understand today's direction.",
            reason="Logged data is ready enough to review validated report guidance.",
            priority=5,
            workflow_target="reports_guidance",
            severity="success",
            evidence={"scenario": "aligned_managed"},
        ),
        DailyNextAction(
            action_id=DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
            title="Review nutrition target progress",
            summary="Check what nutrition target-vs-actual can safely show today.",
            reason="Review approved nutrition progress before changing the plan.",
            priority=6,
            workflow_target="nutrition_target_vs_actual",
            severity="info",
            evidence={"scenario": "nutrition_training_mismatch"},
        ),
    ]


def _recovery_contract(state: str) -> RecoveryAwareCoachCopyContract | None:
    if state == "none":
        return None

    pressure = {
        "unavailable": "unknown",
        "limited": "moderate",
        "usable_low_pressure": "low",
        "usable_moderate_pressure": "moderate",
        "usable_high_pressure": "high",
    }[state]
    recovery_v2_available = state != "unavailable"
    confidence = (
        "Limited"
        if state == "unavailable"
        else "Low"
        if state == "limited"
        else "Moderate"
    )
    data_quality_status = (
        "missing"
        if state == "unavailable"
        else "partial"
        if state == "limited"
        else "usable"
    )

    allowed_claims = [
        (
            "Recovery v2 is unavailable, so recovery-aware copy should not make "
            "specific recovery claims."
        )
    ]
    required_caveats: list[str] = []
    if recovery_v2_available:
        allowed_claims = [
            f"Recent recovery pressure appears {pressure} based on available check-in data."
        ]
    if state in {"unavailable", "limited"}:
        required_caveats = [
            "Mention that available check-in data is limited, partial, missing, or unavailable."
        ]

    return RecoveryAwareCoachCopyContract(
        user_id=102,
        target_date="2026-06-20",
        recovery_v2_available=recovery_v2_available,
        recovery_classification="unknown" if state == "unavailable" else "manageable",
        recovery_pressure=pressure,
        confidence=confidence,
        data_quality_status=data_quality_status,
        allowed_recovery_claims=allowed_claims,
        required_caveats=required_caveats,
        forbidden_claims=[
            "medical or diagnostic claims",
            "forced training-load changes",
            "training-progression changes",
            "unsupported training-safety claims",
        ],
        copy_tone_guidance=[
            "Use bounded wording such as appears, suggests, and based on available check-ins."
        ],
        reason_codes=["copy_matrix_state", state],
        limitations=required_caveats,
        source_services=["daily_coach_today_card_copy_matrix_test"],
    )


def _assert_public_copy_safe(public_payload: dict[str, object]) -> None:
    public_text = str(public_payload).lower()
    for term in PUBLIC_FORBIDDEN_TERMS:
        assert term not in public_text
    for term in UNSAFE_PUBLIC_COPY_TERMS:
        assert term not in public_text
    assert (
        len(str(public_payload["coach_note"]))
        <= DAILY_COACH_TODAY_CARD_MAX_NOTE_CHARACTERS
    )


@pytest.mark.parametrize(
    "action", _approved_actions(), ids=lambda action: action.action_id
)
@pytest.mark.parametrize("state", RECOVERY_MATRIX_STATES)
def test_daily_coach_note_copy_matrix_preserves_safe_public_payload_and_next_action(
    action: DailyNextAction,
    state: str,
) -> None:
    no_contract_card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
    )
    contract = _recovery_contract(state)

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
        recovery_copy_contract=contract,
    )

    assert validate_daily_coach_today_card(card) == []
    public_payload = card.to_public_dict()
    _assert_public_copy_safe(public_payload)

    assert card.next_action_id == no_contract_card.next_action_id == action.action_id
    assert card.next_action_title == no_contract_card.next_action_title == action.title
    assert (
        card.workflow_target
        == no_contract_card.workflow_target
        == action.workflow_target
    )
    assert card.cta_target == no_contract_card.cta_target == action.workflow_target
    assert (
        card.cta_label == no_contract_card.cta_label == f"Next action: {action.title}"
    )
    assert (
        card.supporting_reason == no_contract_card.supporting_reason == action.summary
    )
    assert card.is_provider_generated is False
    assert card.developer_metadata["normal_today_load_calls_provider"] is False
    assert card.developer_metadata["narrative_persisted"] is False


@pytest.mark.parametrize(
    ("state", "expected_phrase"),
    [
        (
            "unavailable",
            (
                "Recovery context is limited today, so keep the note grounded in "
                "the next action above."
            ),
        ),
        (
            "limited",
            (
                "Recovery context is limited today, so keep the note grounded in "
                "the next action above."
            ),
        ),
        (
            "usable_low_pressure",
            "Recent check-ins suggest recovery pressure is low",
        ),
        (
            "usable_moderate_pressure",
            "Available check-in data suggests recovery pressure is moderate",
        ),
        (
            "usable_high_pressure",
            "Available check-in data suggests recovery pressure is high",
        ),
    ],
)
def test_recovery_pressure_copy_paths_are_bounded_and_expected(
    state: str,
    expected_phrase: str,
) -> None:
    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=_approved_actions()[3],
        recovery_copy_contract=_recovery_contract(state),
    )

    public_note = card.to_public_dict()["coach_note"]

    assert expected_phrase in public_note
    assert "diagnosis" not in public_note.lower()
    assert "automatic" not in public_note.lower()
    assert validate_daily_coach_today_card(card) == []


def test_serialized_recovery_contract_dict_path_matches_object_path() -> None:
    action = _approved_actions()[2]
    contract = _recovery_contract("usable_high_pressure")
    assert contract is not None

    object_card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
        recovery_copy_contract=contract,
    )
    dict_card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
        recovery_copy_contract=contract.to_dict(),
    )

    assert dict_card.to_public_dict() == object_card.to_public_dict()
    assert dict_card.to_developer_dict()["next_action_id"] == action.action_id
    assert validate_daily_coach_today_card(dict_card) == []


def test_no_contract_today_card_behavior_remains_backward_compatible() -> None:
    action = _approved_actions()[3]

    card = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
    )

    assert card.coach_note == (
        "Today is a good day to review the approved workout before you start. "
        "Check the plan first so the session stays tied to the current training "
        "and recovery context."
    )
    assert card.developer_metadata["recovery_copy_contract_supplied"] is False
    assert card.developer_metadata["recovery_copy_contract_used"] is False
    assert validate_daily_coach_today_card(card) == []


def test_public_copy_is_deterministic_for_same_inputs() -> None:
    action = _approved_actions()[1]
    contract = _recovery_contract("usable_moderate_pressure")

    first = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
        recovery_copy_contract=contract,
    )
    second = build_daily_coach_today_card(
        102,
        target_date="2026-06-20",
        action=action,
        recovery_copy_contract=contract,
    )

    assert first.to_public_dict() == second.to_public_dict()
    assert first.to_developer_dict()["display_source"] == "deterministic_today_card"
    assert second.to_developer_dict()["display_source"] == "deterministic_today_card"


def test_matrix_documentation_records_uncaged_provider_voice_direction() -> None:
    milestone_doc = Path(
        "docs/project_memory/milestones/daily_coach_note_copy_qa_matrix_v1.md"
    ).read_text(encoding="utf-8")

    assert "This milestone cages evaluation, not model voice." in milestone_doc
    assert "repeated-template risk" in milestone_doc
    assert "raw deterministic backend data" in milestone_doc
    assert "not only backend-written prose summaries" in milestone_doc
    assert (
        "do not force the model to choose from approved sentence templates"
        in milestone_doc
    )
    assert (
        "Provider output does not change workouts, nutrition, recommendations, "
        "or Daily Next Action selection."
    ) in milestone_doc
