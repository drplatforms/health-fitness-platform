from __future__ import annotations

from collections.abc import Sequence

from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    ClaimAuditFinding,
    ClaimAuditResult,
    ExtractedDraftClaim,
)


def audit_extracted_draft_claims(
    claims: Sequence[ExtractedDraftClaim],
    brief: ApprovedCoachBrief,
) -> ClaimAuditResult:
    findings: list[ClaimAuditFinding] = []
    for claim in claims:
        finding = _finding_for_claim(claim, brief)
        if finding is not None:
            findings.append(finding)

    passed = not findings
    repairable = bool(findings) and all(finding.repairable for finding in findings)
    if passed:
        decision = "approve"
    elif repairable:
        decision = "repair_required"
    else:
        decision = "fallback_required"
    return ClaimAuditResult(
        passed=passed,
        findings=tuple(findings),
        repairable=repairable,
        final_decision=decision,  # type: ignore[arg-type]
        unsupported_claim_count=sum(
            1 for item in findings if item.finding_type.startswith("unsupported_")
        ),
        food_claim_count=sum(
            1 for claim in claims if claim.claim_type.startswith("food")
        ),
        causal_claim_count=sum(
            1 for claim in claims if claim.claim_type == "causal_claim"
        ),
        addressing_violation_count=sum(
            1 for item in findings if item.finding_type == "addressing_policy_violation"
        ),
    )


def _finding_for_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    if claim.claim_type == "food_identity_claim":
        return _audit_food_claim(claim, brief)
    if claim.claim_type == "macro_status_claim":
        return _audit_macro_claim(claim, brief)
    if claim.claim_type == "serving_amount_claim":
        return _audit_serving_claim(claim, brief)
    if claim.claim_type == "timing_claim":
        return _audit_timing_claim(claim, brief)
    if claim.claim_type == "training_intensity_claim":
        return _audit_training_claim(claim, brief)
    if claim.claim_type == "recovery_interpretation_claim":
        return _audit_recovery_claim(claim, brief)
    if claim.claim_type == "causal_claim":
        return _audit_causal_claim(claim, brief)
    if claim.claim_type == "addressing_claim":
        return _audit_addressing_claim(claim, brief)
    if claim.claim_type == "medical_or_body_claim":
        return _fail(
            claim,
            finding_type="medical_or_body_claim",
            reason="Medical/body-composition claims are outside the approved brief.",
            required_support="Explicit approved medical/body claim, which v1 does not provide.",
            repair_instruction="Remove the medical/body claim entirely.",
            repairable=False,
        )
    if claim.claim_type == "unsupported_motivation_or_judgment_claim":
        return _fail(
            claim,
            finding_type="unsupported_judgment_claim",
            reason="Judgmental motivation language is not approved coaching context.",
            required_support="None. This language should not appear.",
            repair_instruction="Remove the judgmental language.",
            repairable=True,
        )
    return None


def _audit_food_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    normalized = claim.normalized_claim
    for action in brief.approved_food_actions:
        friendly = _normalize(action.friendly_name or "")
        canonical = _normalize(action.canonical_name or "")
        blocked = {_normalize(item) for item in action.blocked_user_facing_names}
        if normalized in blocked or (
            canonical and normalized == canonical and friendly
        ):
            return _fail(
                claim,
                finding_type="canonical_food_label_visible",
                reason="A canonical food label was used where a friendly food name exists.",
                required_support="Use the approved friendly food display name instead.",
                available_support=(action.food_claim_key,),
                repair_instruction=f"Replace {claim.text_span!r} with {action.friendly_name!r}.",
                repairable=True,
            )
        if friendly and normalized == friendly:
            return None
    return _fail(
        claim,
        finding_type="unsupported_food_claim",
        reason="The draft names a food that is not approved in the coach brief.",
        required_support="ApprovedFoodAction with matching friendly_name.",
        repair_instruction="Remove the unapproved food name.",
        repairable=False,
    )


def _audit_macro_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    macro = claim.normalized_claim.split("_", 1)[0]
    support = tuple(
        fact.claim_key
        for fact in brief.approved_facts
        if fact.claim_key.startswith(f"nutrition.{macro}.")
    )
    if support:
        return None
    return _fail(
        claim,
        finding_type="unsupported_macro_status_claim",
        reason="The draft mentions a macro gap/status not present in the approved brief.",
        required_support=f"nutrition.{macro}.status or equivalent approved macro claim",
        repair_instruction="Remove the macro status/gap claim.",
        repairable=True,
    )


def _audit_serving_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    normalized = _normalize(claim.text_span)
    for action in brief.approved_food_actions:
        if action.serving_allowed and action.serving_display:
            if normalized == _normalize(action.serving_display):
                return None
    return _fail(
        claim,
        finding_type="invented_serving_amount",
        reason="Serving amounts are allowed only when explicitly approved in the brief.",
        required_support="ApprovedFoodAction.serving_display with serving_allowed=true",
        repair_instruction="Remove the serving amount.",
        repairable=False,
    )


def _audit_timing_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    for action in brief.approved_food_actions:
        if any(
            _normalize(claim.text_span) in _normalize(item)
            for item in action.allowed_conditions
        ):
            return None
    return _fail(
        claim,
        finding_type="invented_timing_claim",
        reason="Timing is allowed only when explicitly approved in the brief.",
        required_support="Approved timing condition in ApprovedFoodAction.allowed_conditions.",
        repair_instruction="Remove the timing phrase and keep the action timing-neutral.",
        repairable=True,
    )


def _audit_training_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    if brief.approved_training_actions:
        return None
    return _fail(
        claim,
        finding_type="unsupported_training_claim",
        reason="The draft gives training guidance without approved training action context.",
        required_support="ApprovedTrainingAction in the brief.",
        repair_instruction="Remove the training instruction.",
        repairable=True,
    )


def _audit_recovery_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    normalized = claim.normalized_claim
    if normalized in {"fully recovered", "no fatigue"}:
        return _fail(
            claim,
            finding_type="unsupported_recovery_overclaim",
            reason="The draft overstates recovery status beyond approved interpretation.",
            required_support="Explicit approved recovery overclaim, which v1 should not provide.",
            repair_instruction="Replace with a cautious recovery interpretation or remove it.",
            repairable=True,
        )
    if brief.approved_recovery_interpretations:
        return None
    return _fail(
        claim,
        finding_type="unsupported_recovery_claim",
        reason="The draft mentions recovery/fatigue without approved recovery interpretation.",
        required_support="ApprovedRecoveryInterpretation in the brief.",
        repair_instruction="Remove the recovery interpretation.",
        repairable=True,
    )


def _audit_causal_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    normalized = claim.normalized_claim
    approved = any(
        normalized in _normalize(item) for item in brief.approved_interpretations
    )
    if approved:
        return None
    return _fail(
        claim,
        finding_type="unsupported_causal_claim",
        reason="The draft makes a causal claim that is not in the approved brief.",
        required_support="Approved causal interpretation in ApprovedCoachBrief.approved_interpretations.",
        repair_instruction="Rewrite without causal language. Keep the approved status/action but remove the cause-effect claim.",
        repairable=True,
    )


def _audit_addressing_claim(
    claim: ExtractedDraftClaim, brief: ApprovedCoachBrief
) -> ClaimAuditFinding | None:
    if brief.addressing_policy.allow_name:
        preferred = _normalize(brief.addressing_policy.preferred_name or "")
        if preferred and claim.normalized_claim == preferred:
            return None
    return _fail(
        claim,
        finding_type="addressing_policy_violation",
        reason="Personal name use is forbidden unless explicitly approved.",
        required_support="AddressingPolicy.allow_name=true with matching preferred_name.",
        repair_instruction="Remove the personal name and address the user directly without naming them.",
        repairable=True,
    )


def _fail(
    claim: ExtractedDraftClaim,
    *,
    finding_type: str,
    reason: str,
    required_support: str,
    available_support: tuple[str, ...] = (),
    repair_instruction: str | None,
    repairable: bool,
) -> ClaimAuditFinding:
    return ClaimAuditFinding(
        finding_type=finding_type,
        severity="fail" if repairable else "block",
        text_span=claim.text_span,
        extracted_claim=claim.normalized_claim,
        reason=reason,
        required_support=required_support,
        available_support=available_support,
        repair_instruction=repair_instruction,
        repairable=repairable,
    )


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())
