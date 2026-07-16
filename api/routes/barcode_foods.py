from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.barcode_food_service import (
    materialize_barcode_food,
    resolve_barcode_food,
)

router = APIRouter()


class BarcodeResolveRequest(BaseModel):
    barcode: str
    barcode_format: str | None = None


class BarcodeMaterializeRequest(BaseModel):
    raw_food_source_record_id: int
    normalized_gtin: str


@router.post("/foods/barcode/resolve")
def resolve_barcode_food_endpoint(request: BarcodeResolveRequest):
    """Resolve a barcode locally first, then through bounded branded-food providers."""

    return resolve_barcode_food(
        request.barcode,
        request.barcode_format,
    ).to_public_dict()


@router.post("/foods/barcode/materialize")
def materialize_barcode_food_endpoint(request: BarcodeMaterializeRequest):
    """Confirm a server-owned raw barcode candidate into the canonical catalog."""

    return materialize_barcode_food(
        request.raw_food_source_record_id,
        request.normalized_gtin,
    ).to_public_dict()
