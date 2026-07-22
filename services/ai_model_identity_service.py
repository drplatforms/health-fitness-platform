from __future__ import annotations

import re
from datetime import date

KNOWN_OPENAI_TEXT_MODEL_FAMILIES = (
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.4-nano",
)

_SNAPSHOT_DATE_PATTERN = r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"


def canonical_openai_model_family(model: str) -> str | None:
    """Resolve only known model families and their explicit dated snapshots."""

    if not isinstance(model, str):
        return None
    candidate = model.strip()
    if candidate in KNOWN_OPENAI_TEXT_MODEL_FAMILIES:
        return candidate
    for family in KNOWN_OPENAI_TEXT_MODEL_FAMILIES:
        snapshot_match = re.fullmatch(
            rf"{re.escape(family)}-{_SNAPSHOT_DATE_PATTERN}",
            candidate,
        )
        if snapshot_match is not None:
            snapshot_date = candidate.removeprefix(f"{family}-")
            try:
                date.fromisoformat(snapshot_date)
            except ValueError:
                continue
            return family
    return None
