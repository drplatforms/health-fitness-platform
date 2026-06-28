from __future__ import annotations

from models.daily_coach_natural_draft_audit_models import NaturalCoachDraft
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_claim_audit_service import audit_extracted_draft_claims
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from tests.test_daily_coach_approved_brief_service import FakeSynthesis, _value_context


def _audit(text: str):
    brief = build_approved_coach_brief(
        user_id=102,
        target_date="2026-06-05",
        scenario_id="rich_nutrition_training_recovery",
        synthesis=FakeSynthesis(),
        value_context=_value_context(),
    )
    draft = NaturalCoachDraft(headline="Daily Coach", body=text)
    return audit_extracted_draft_claims(
        extract_claims_from_natural_draft(draft, brief), brief
    )


def test_claim_audit_allows_approved_plain_claims() -> None:
    audit = _audit(
        "Recovery looks good enough to train as planned. Keep a couple reps in reserve. "
        "Protein is below target. Add canned tuna if protein is still short."
    )

    assert audit.passed is True
    assert audit.final_decision == "approve"


def test_claim_audit_rejects_canonical_food_label_and_hardcoded_name() -> None:
    audit = _audit("Dustin, add Tuna, Canned in Water if protein is still short.")

    assert audit.passed is False
    assert audit.repairable is True
    finding_types = {finding.finding_type for finding in audit.findings}
    assert "canonical_food_label_visible" in finding_types
    assert "addressing_policy_violation" in finding_types


def test_claim_audit_blocks_invented_serving_and_medical_claim() -> None:
    audit = _audit("Add one can of canned tuna. This prevents muscle loss.")

    assert audit.passed is False
    assert audit.repairable is False
    finding_types = {finding.finding_type for finding in audit.findings}
    assert "invented_serving_amount" in finding_types
    assert "medical_or_body_claim" in finding_types


def test_claim_audit_rejects_unsupported_causal_claim() -> None:
    audit = _audit("Low protein is hurting recovery, so add canned tuna.")

    assert audit.passed is False
    assert audit.repairable is True
    assert "unsupported_causal_claim" in {
        finding.finding_type for finding in audit.findings
    }
