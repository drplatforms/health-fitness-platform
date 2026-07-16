from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

BarcodeResolveStatus = Literal[
    "resolved",
    "candidate",
    "not_found",
    "incomplete",
    "provider_unavailable",
    "conflict",
    "invalid_barcode",
]

ProviderLookupStatus = Literal["found", "incomplete", "not_found", "unavailable"]


@dataclass(frozen=True)
class NormalizedBarcode:
    barcode_input: str
    barcode_format: str | None
    normalized_gtin: str
    lookup_variants: tuple[str, ...]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "barcode_input": self.barcode_input,
            "barcode_format": self.barcode_format,
            "normalized_gtin": self.normalized_gtin,
            "lookup_variants": list(self.lookup_variants),
        }


@dataclass(frozen=True)
class BarcodeFoodCandidate:
    source_name: str
    source_record_id: str
    barcode: str
    normalized_gtin: str
    product_name: str
    brand_name: str | None
    calories_per_100g: float | None
    protein_g_per_100g: float | None
    carbs_g_per_100g: float | None
    fat_g_per_100g: float | None
    serving_size: float | None = None
    serving_size_unit: str | None = None
    serving_label: str | None = None
    food_category: str | None = None
    raw_food_source_record_id: int | None = None
    license: str | None = None
    source_url: str | None = None
    source_payload: dict[str, Any] = field(default_factory=dict, repr=False)

    def nutrient_summary(self) -> dict[str, float | None]:
        return {
            "calories_per_100g": self.calories_per_100g,
            "protein_g_per_100g": self.protein_g_per_100g,
            "carbohydrate_g_per_100g": self.carbs_g_per_100g,
            "fat_g_per_100g": self.fat_g_per_100g,
        }

    def to_public_dict(self) -> dict[str, object]:
        return {
            "raw_food_source_record_id": self.raw_food_source_record_id,
            "normalized_gtin": self.normalized_gtin,
            "barcode": self.barcode,
            "product_name": self.product_name,
            "brand_name": self.brand_name,
            "source_name": self.source_name,
            "source_record_id": self.source_record_id,
            "nutrient_summary": self.nutrient_summary(),
            "serving_label": self.serving_label,
            "serving_grams": (
                self.serving_size
                if (self.serving_size_unit or "").strip().casefold()
                in {"g", "gram", "grams"}
                else None
            ),
        }


@dataclass(frozen=True)
class ProviderLookupResult:
    status: ProviderLookupStatus
    provider: str
    candidate: BarcodeFoodCandidate | None = None
    reason: str | None = None


@dataclass(frozen=True)
class BarcodeResolveResult:
    status: BarcodeResolveStatus
    normalized_barcode: NormalizedBarcode | None = None
    provider: str | None = None
    canonical_food: dict[str, object] | None = None
    candidate: BarcodeFoodCandidate | None = None
    reason: str | None = None
    conflict_canonical_food_ids: tuple[int, ...] = ()

    def to_public_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "provider": self.provider,
            "reason": self.reason,
        }
        if self.normalized_barcode is not None:
            payload.update(self.normalized_barcode.to_public_dict())
        if self.canonical_food is not None:
            payload["canonical_food"] = self.canonical_food
        if self.candidate is not None:
            payload["candidate"] = self.candidate.to_public_dict()
        if self.conflict_canonical_food_ids:
            payload["conflict"] = {
                "canonical_food_ids": list(self.conflict_canonical_food_ids)
            }
        return payload
