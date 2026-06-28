from __future__ import annotations

import re
from collections.abc import Iterable

from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    ExtractedDraftClaim,
    NaturalCoachDraft,
)

_MACROS = ("calories", "protein", "carbs", "fat")
_SERVING_PATTERNS = (
    r"\b\d+(?:\.\d+)?\s*g\b",
    r"\bone can\b",
    r"\bone packet\b",
    r"\bhalf cup\b",
    r"\bone scoop\b",
    r"\bone bowl\b",
    r"\bone serving\b",
    r"\bhandful\b",
    r"\bplate\b",
)
_TIMING_PATTERNS = (
    "after training",
    "post-workout",
    "post workout",
    "before bed",
    "with dinner",
    "before training",
)
_TRAINING_PATTERNS = (
    "train as planned",
    "planned session",
    "planned workout",
    "reps in reserve",
    "rir",
    "max-effort",
    "max effort",
    "turns into a grind",
    "failure",
    "push harder",
    "back off",
    "deload",
)
_RECOVERY_PATTERNS = (
    "recovery looks good",
    "readiness",
    "fatigue",
    "fully recovered",
    "no fatigue",
    "under-recovered",
    "back off today",
)
_CAUSAL_PATTERNS = (
    "because",
    "caused",
    "due to",
    "leads to",
    "helps recovery",
    "hurts recovery",
    "hurting recovery",
    "improves performance",
    "compromising",
    "support muscle growth",
    "affecting recovery",
)
_MEDICAL_PATTERNS = (
    "injury",
    "hormones",
    "metabolism",
    "overtraining",
    "muscle loss",
    "disease",
    "diagnose",
)
_JUDGMENT_PATTERNS = (
    "you failed",
    "need discipline",
    "wasted the workout",
    "you are underfed",
)


def extract_claims_from_natural_draft(
    draft: NaturalCoachDraft,
    brief: ApprovedCoachBrief,
) -> list[ExtractedDraftClaim]:
    text = f"{draft.headline}\n{draft.body}"
    claims: list[ExtractedDraftClaim] = []
    claims.extend(_extract_food_claims(text, brief))
    claims.extend(_extract_macro_claims(text, brief))
    claims.extend(
        _extract_regex_patterns(text, _SERVING_PATTERNS, "serving_amount_claim")
    )
    claims.extend(_extract_phrase_patterns(text, _TIMING_PATTERNS, "timing_claim"))
    claims.extend(
        _extract_phrase_patterns(text, _TRAINING_PATTERNS, "training_intensity_claim")
    )
    claims.extend(
        _extract_phrase_patterns(
            text, _RECOVERY_PATTERNS, "recovery_interpretation_claim"
        )
    )
    claims.extend(_extract_phrase_patterns(text, _CAUSAL_PATTERNS, "causal_claim"))
    claims.extend(
        _extract_phrase_patterns(text, _MEDICAL_PATTERNS, "medical_or_body_claim")
    )
    claims.extend(
        _extract_phrase_patterns(
            text, _JUDGMENT_PATTERNS, "unsupported_motivation_or_judgment_claim"
        )
    )
    claims.extend(_extract_addressing_claims(text, brief))
    claims.extend(_extract_limitation_claims(text))
    return _dedupe_claims(claims)


def _extract_food_claims(
    text: str, brief: ApprovedCoachBrief
) -> list[ExtractedDraftClaim]:
    claims: list[ExtractedDraftClaim] = []
    for action in brief.approved_food_actions:
        food_terms = []
        if action.friendly_name:
            food_terms.append((action.friendly_name, action.food_claim_key))
        if action.canonical_name:
            food_terms.append((action.canonical_name, action.food_claim_key))
        for blocked in action.blocked_user_facing_names:
            food_terms.append((blocked, action.food_claim_key))
        for term, claim_key in food_terms:
            if _contains_phrase(text, term):
                claims.append(
                    ExtractedDraftClaim(
                        claim_type="food_identity_claim",
                        text_span=term,
                        normalized_claim=_normalize(term),
                        claim_keys_matched=(claim_key,),
                        confidence="high",
                    )
                )
    return claims


def _extract_macro_claims(
    text: str, brief: ApprovedCoachBrief
) -> list[ExtractedDraftClaim]:
    claims: list[ExtractedDraftClaim] = []
    normalized = _normalize(text)
    for macro in _MACROS:
        patterns = [
            f"{macro} is below target",
            f"{macro} are below target",
            f"{macro} below target",
            f"{macro} is still short",
            f"{macro} are still short",
            f"{macro} still short",
            f"{macro} gap",
        ]
        if any(pattern in normalized for pattern in patterns):
            keys = tuple(
                fact.claim_key
                for fact in brief.approved_facts
                if fact.claim_key.startswith(f"nutrition.{macro}.")
            )
            claims.append(
                ExtractedDraftClaim(
                    claim_type="macro_status_claim",
                    text_span=macro,
                    normalized_claim=f"{macro}_status_or_gap",
                    claim_keys_matched=keys,
                    confidence="high",
                )
            )
    return claims


def _extract_regex_patterns(
    text: str, patterns: Iterable[str], claim_type: str
) -> list[ExtractedDraftClaim]:
    claims: list[ExtractedDraftClaim] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            claims.append(
                ExtractedDraftClaim(
                    claim_type=claim_type,
                    text_span=match.group(0),
                    normalized_claim=_normalize(match.group(0)),
                    confidence="high",
                )
            )
    return claims


def _extract_phrase_patterns(
    text: str, patterns: Iterable[str], claim_type: str
) -> list[ExtractedDraftClaim]:
    claims: list[ExtractedDraftClaim] = []
    normalized = _normalize(text)
    for pattern in patterns:
        if pattern in normalized:
            claims.append(
                ExtractedDraftClaim(
                    claim_type=claim_type,
                    text_span=pattern,
                    normalized_claim=pattern,
                    confidence="medium",
                )
            )
    return claims


def _extract_addressing_claims(
    text: str, brief: ApprovedCoachBrief
) -> list[ExtractedDraftClaim]:
    names = ["dustin"]
    if brief.addressing_policy.preferred_name:
        names.append(brief.addressing_policy.preferred_name.lower())
    claims = []
    normalized = _normalize(text)
    for name in sorted(set(names)):
        if name and re.search(rf"\b{re.escape(name)}\b", normalized):
            claims.append(
                ExtractedDraftClaim(
                    claim_type="addressing_claim",
                    text_span=name,
                    normalized_claim=name,
                    confidence="high",
                )
            )
    return claims


def _extract_limitation_claims(text: str) -> list[ExtractedDraftClaim]:
    claims: list[ExtractedDraftClaim] = []
    normalized = _normalize(text)
    for phrase in [
        "logging is incomplete",
        "not enough food data",
        "training details are missing",
    ]:
        if phrase in normalized:
            claims.append(
                ExtractedDraftClaim(
                    claim_type="limitation_claim",
                    text_span=phrase,
                    normalized_claim=phrase,
                    confidence="medium",
                )
            )
    return claims


def _dedupe_claims(claims: list[ExtractedDraftClaim]) -> list[ExtractedDraftClaim]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ExtractedDraftClaim] = []
    for claim in claims:
        key = (claim.claim_type, claim.normalized_claim)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped


def _contains_phrase(text: str, phrase: str) -> bool:
    return _normalize(phrase) in _normalize(text)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
