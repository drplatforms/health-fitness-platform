from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PersonalFoodInputBasis = Literal["nutrition_label", "per_100g"]


@dataclass(frozen=True)
class PersonalFoodRevisionInput:
    input_basis: PersonalFoodInputBasis | str
    display_name: str | None = None
    brand_name: str | None = None
    serving_name: str | None = None
    serving_grams: float | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    source_note: str | None = None


@dataclass(frozen=True)
class PersonalFoodRevision:
    id: int
    personal_food_id: int
    revision_number: int
    display_name_snapshot: str
    brand_name_snapshot: str | None
    input_basis: PersonalFoodInputBasis
    serving_name: str | None
    serving_grams: float | None
    calories_per_100g: float | None
    protein_g_per_100g: float | None
    carbs_g_per_100g: float | None
    fat_g_per_100g: float | None
    entered_calories: float | None
    entered_protein_g: float | None
    entered_carbs_g: float | None
    entered_fat_g: float | None
    source_note: str | None
    legacy_food_id: int
    created_at: str

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("legacy_food_id")
        return payload

    def to_revision_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "revision_number": self.revision_number,
            "display_name_snapshot": self.display_name_snapshot,
            "brand_name_snapshot": self.brand_name_snapshot,
            "input_basis": self.input_basis,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class PersonalFood:
    id: int
    user_id: int
    display_name: str
    normalized_name: str
    brand_name: str | None
    active: bool
    current_revision_id: int
    created_at: str
    updated_at: str
    current_revision: PersonalFoodRevision
    revisions: tuple[PersonalFoodRevision, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "brand_name": self.brand_name,
            "active": self.active,
            "current_revision_id": self.current_revision_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_revision": self.current_revision.to_public_dict(),
            "revisions": [
                revision.to_revision_summary() for revision in self.revisions
            ],
        }


@dataclass(frozen=True)
class PersonalFoodLogResult:
    logged_food_entry_id: int
    personal_food_id: int
    personal_food_revision_id: int
    display_name: str
    grams: float
    serving_quantity: float | None
    logged_date: str
    meal_type: str | None
    nutrient_summary: dict[str, float]

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.serving_quantity is None:
            payload.pop("serving_quantity")
        if self.meal_type is None:
            payload.pop("meal_type")
        return payload
