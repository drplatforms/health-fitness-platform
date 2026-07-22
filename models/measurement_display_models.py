from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TrustedQuantityMeasure:
    unit_name: str
    unit_quantity: float
    grams: float
    confidence: str
    source: str | None = None
    source_note: str | None = None
    serving_unit_id: int | None = None
    sort_order: int = 100


@dataclass(frozen=True)
class QuantityPresentation:
    canonical_grams: float
    primary_quantity: str
    primary_unit: str
    primary_text: str
    secondary_grams: float | None
    secondary_text: str | None
    display_text: str
    conversion_source: str
    reliability: str
    source: str | None = None
    source_note: str | None = None
    serving_unit_id: int | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)
