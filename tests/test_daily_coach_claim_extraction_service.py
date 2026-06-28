from __future__ import annotations

from models.daily_coach_natural_draft_audit_models import NaturalCoachDraft
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from tests.test_daily_coach_approved_brief_service import FakeSynthesis, _value_context


def _brief():
    return build_approved_coach_brief(
        user_id=102,
        target_date="2026-06-05",
        scenario_id="rich_nutrition_training_recovery",
        synthesis=FakeSynthesis(),
        value_context=_value_context(),
    )


def test_claim_extraction_detects_high_risk_claims() -> None:
    draft = NaturalCoachDraft(
        headline="Dustin, train clean",
        body=(
            "Protein is still short. Add Tuna, Canned in Water after training. "
            "Use one can because low protein is hurting recovery. "
            "Keep a couple reps in reserve. You are fully recovered."
        ),
    )

    claims = extract_claims_from_natural_draft(draft, _brief())
    claim_types = {claim.claim_type for claim in claims}

    assert "food_identity_claim" in claim_types
    assert "macro_status_claim" in claim_types
    assert "serving_amount_claim" in claim_types
    assert "timing_claim" in claim_types
    assert "training_intensity_claim" in claim_types
    assert "recovery_interpretation_claim" in claim_types
    assert "causal_claim" in claim_types
    assert "addressing_claim" in claim_types
