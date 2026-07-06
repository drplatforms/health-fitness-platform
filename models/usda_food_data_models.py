from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsdaFoodImportRow:
    fdc_id: int
    description: str
    data_type: str
    calories_per_100g: float | None
    protein_g_per_100g: float | None
    carbs_g_per_100g: float | None
    fat_g_per_100g: float | None
    brand_owner: str | None = None
    gtin_upc: str | None = None
    serving_size: float | None = None
    serving_size_unit: str | None = None
    food_category: str | None = None


@dataclass(frozen=True)
class UsdaFoodImportSummary:
    input_path: str
    database_path: str
    source_name: str
    import_batch: str
    total_rows: int
    inserted_count: int
    updated_count: int
