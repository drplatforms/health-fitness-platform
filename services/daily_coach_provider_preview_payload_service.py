from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from models.daily_coach_intelligence_models import DailyCoachIntelligenceSnapshot
from models.daily_coach_provider_preview_payload_models import (
    DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION,
    DailyCoachProviderPreviewRawDataPayload,
)
from services.daily_coach_intelligence_snapshot_service import (
    build_daily_coach_intelligence_snapshot,
)

BACKEND_TRUTH_CONTRACT: dict[str, bool] = {
    "backend_owns_facts": True,
    "backend_owns_confidence": True,
    "backend_owns_limitations": True,
    "backend_owns_persistence": True,
    "backend_owns_recommendations": True,
    "provider_output_is_not_truth": True,
    "provider_output_may_not_mutate_state": True,
    "provider_output_may_not_change_daily_next_action": True,
    "provider_output_may_not_change_workout_plan": True,
    "provider_output_may_not_change_nutrition_targets": True,
}

PROVIDER_VOICE_SPACE: dict[str, Any] = {
    "voice_goal": "natural_coaching_language_from_backend_facts",
    "do_not_force_sentence_bank": True,
    "do_not_reduce_input_to_backend_prose_summary": True,
    "allow_varied_sentence_structure": True,
    "allow_synthesis_from_source_sections": True,
    "grounding_required": True,
    "developer_preview_only": True,
}

PROVIDER_INPUT_GUIDANCE: dict[str, Any] = {
    "input_role": "developer_preview_raw_data_payload",
    "use_source_sections_first": True,
    "treat_backend_facts_as_source_of_truth": True,
    "treat_confidence_limitations_and_gaps_as_binding_context": True,
    "natural_voice_allowed_later": True,
    "final_copy_authorized": False,
    "normal_today_surface_authorized": False,
    "provider_call_authorized_by_this_payload": False,
    "sentence_bank_authorized": False,
}

FORBIDDEN_PROVIDER_AUTHORITY: list[str] = [
    "change Daily Next Action selection",
    "change workout plan",
    "change nutrition targets",
    "persist narrative",
    "write to database",
    "call provider from normal Today load",
    "diagnose",
    "treat",
    "claim injury",
    "claim illness",
    "claim unsafe to train",
    "force deload",
    "force progression",
    "invent facts",
    "invent calories or protein targets",
    "hide confidence or limitations",
]

_SOURCE_DATA_KEYS = (
    "recovery_intelligence",
    "recovery_intelligence_v2",
    "workout_set_intelligence",
    "training_execution_summary",
    "nutrition_trend_window",
    "foundation_layer_status",
    "data_completeness",
    "source_data_gaps",
    "reason_codes",
    "limitations",
)


def build_daily_coach_provider_preview_raw_data_payload(
    snapshot: DailyCoachIntelligenceSnapshot | Mapping[str, Any],
) -> DailyCoachProviderPreviewRawDataPayload:
    """Build a developer-only raw data payload for future provider preview.

    This service wraps the existing backend-owned Daily Coach Intelligence Snapshot.
    It does not call a provider, render Daily Coach Note copy, mutate state, persist
    output, or authorize product-surface display.
    """

    snapshot_dict = _snapshot_to_dict(snapshot)
    source_data = {key: snapshot_dict.get(key) for key in _SOURCE_DATA_KEYS}

    return DailyCoachProviderPreviewRawDataPayload(
        payload_version=DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION,
        user_id=int(snapshot_dict["user_id"]),
        target_date=str(snapshot_dict["target_date"]),
        generated_at=datetime.now(UTC).isoformat(),
        developer_preview_only=True,
        provider_call_allowed=False,
        persistence_allowed=False,
        product_surface_allowed=False,
        source_snapshot_version=str(snapshot_dict["snapshot_version"]),
        source_services=list(snapshot_dict.get("source_services") or []),
        source_data=source_data,
        data_completeness=dict(snapshot_dict.get("data_completeness") or {}),
        source_data_gaps=list(snapshot_dict.get("source_data_gaps") or []),
        reason_codes=list(snapshot_dict.get("reason_codes") or []),
        limitations=list(snapshot_dict.get("limitations") or []),
        backend_truth_contract=dict(BACKEND_TRUTH_CONTRACT),
        provider_voice_space=dict(PROVIDER_VOICE_SPACE),
        provider_input_guidance=dict(PROVIDER_INPUT_GUIDANCE),
        forbidden_provider_authority=list(FORBIDDEN_PROVIDER_AUTHORITY),
    )


def build_daily_coach_provider_preview_raw_data_payload_from_snapshot(
    snapshot: DailyCoachIntelligenceSnapshot | Mapping[str, Any],
) -> DailyCoachProviderPreviewRawDataPayload:
    return build_daily_coach_provider_preview_raw_data_payload(snapshot)


def build_daily_coach_provider_preview_raw_data_payload_for_user(
    *,
    user_id: int,
    target_date: str | None = None,
) -> DailyCoachProviderPreviewRawDataPayload:
    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=user_id,
        target_date=target_date,
    )
    return build_daily_coach_provider_preview_raw_data_payload(snapshot)


def _snapshot_to_dict(
    snapshot: DailyCoachIntelligenceSnapshot | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(snapshot, DailyCoachIntelligenceSnapshot):
        return snapshot.to_dict()
    if isinstance(snapshot, Mapping):
        return dict(snapshot)
    if hasattr(snapshot, "to_dict"):
        return snapshot.to_dict()
    return asdict(snapshot)
