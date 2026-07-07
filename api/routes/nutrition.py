# =====================================
# Imports
# =====================================

from datetime import date as date_cls

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nutrition_actuals_confidence_service import (
    build_public_nutrition_actuals_confidence_for_date,
)
from services.nutrition_service import (
    CanonicalFoodInactiveError,
    CanonicalFoodLogEntryNotFoundError,
    CanonicalFoodLoggingError,
    CanonicalFoodNotFoundError,
    add_canonical_food_entry,
    add_food_entry,
    delete_canonical_food_entry,
    get_daily_canonical_food_logs,
    get_daily_canonical_food_macro_totals,
    get_daily_nutrition,
    search_foods,
    update_canonical_food_entry,
)
from services.nutrition_serving_unit_logging_service import (
    ServingUnitFoodMismatchError,
    ServingUnitInactiveError,
    ServingUnitLoggingError,
    ServingUnitNotFoundError,
    log_canonical_food_serving,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Request Models
# =====================================


class NutritionLogRequest(BaseModel):
    user_id: int
    food_id: int
    grams: float


class CanonicalNutritionLogRequest(BaseModel):
    canonical_food_id: int
    grams: float | None = None
    serving_unit_id: int | None = None
    quantity: float | None = None
    entry_date: str | None = None
    meal_type: str | None = None
    notes: str | None = None


class CanonicalNutritionLogUpdateRequest(BaseModel):
    grams: float | None = None
    meal_type: str | None = None
    entry_date: str | None = None


class ServingUnitNutritionLogRequest(BaseModel):
    canonical_food_id: int
    serving_unit_id: int
    quantity: float
    meal: str | None = None
    meal_type: str | None = None
    logged_date: str | None = None
    notes: str | None = None


# =====================================
# Food Search Endpoint
# =====================================


@router.get("/foods/search")
def search_foods_endpoint(query: str):
    foods = search_foods(query)

    return {
        "success": True,
        "foods": foods,
    }


# =====================================
# Nutrition Summary Endpoints
# =====================================


@router.get("/nutrition/{user_id}/actuals-confidence/debug")
def nutrition_actuals_confidence_debug(user_id: int, date: str):
    try:
        date_cls.fromisoformat(date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="date must use YYYY-MM-DD format.",
        ) from exc

    return build_public_nutrition_actuals_confidence_for_date(
        user_id=user_id,
        target_date=date,
    )


@router.get("/nutrition/{user_id}/canonical-totals")
def daily_canonical_food_macro_totals(user_id: int, date: str):
    try:
        totals = get_daily_canonical_food_macro_totals(user_id=user_id, entry_date=date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "date": date,
        "totals": totals,
    }


@router.get("/nutrition/{user_id}/canonical-logs")
def daily_canonical_food_logs(user_id: int, date: str):
    try:
        entries = get_daily_canonical_food_logs(user_id=user_id, entry_date=date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "date": date,
        "entries": entries,
    }


@router.patch("/nutrition/{user_id}/canonical-logs/{entry_id}")
def update_canonical_logged_food_entry(
    user_id: int,
    entry_id: int,
    entry: CanonicalNutritionLogUpdateRequest,
):
    if entry.entry_date is not None:
        try:
            date_cls.fromisoformat(entry.entry_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="entry_date must use YYYY-MM-DD format.",
            ) from exc

    try:
        updated_entry = update_canonical_food_entry(
            user_id=user_id,
            entry_id=entry_id,
            grams=entry.grams,
            meal_type=entry.meal_type,
            entry_date=entry.entry_date,
        )
    except CanonicalFoodLogEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CanonicalFoodLoggingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        "entry": updated_entry,
    }


@router.delete("/nutrition/{user_id}/canonical-logs/{entry_id}")
def delete_canonical_logged_food_entry(
    user_id: int,
    entry_id: int,
    date: str | None = None,
):
    if date is not None:
        try:
            date_cls.fromisoformat(date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="date must use YYYY-MM-DD format.",
            ) from exc

    try:
        deleted_entry = delete_canonical_food_entry(
            user_id=user_id,
            entry_id=entry_id,
            entry_date=date,
        )
    except CanonicalFoodLogEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        **deleted_entry,
    }


@router.get("/nutrition/{user_id}/{entry_date}")
def daily_nutrition(user_id: int, entry_date: str):
    nutrition = get_daily_nutrition(user_id, entry_date)

    return {
        "success": True,
        "nutrition": nutrition,
    }


# =====================================
# Log Food Endpoint
# =====================================


@router.post("/nutrition/log")
def log_food_entry(entry: NutritionLogRequest):
    add_food_entry(
        user_id=entry.user_id,
        food_id=entry.food_id,
        grams=entry.grams,
    )

    return {
        "success": True,
        "message": "Food logged successfully.",
    }


@router.post("/nutrition/{user_id}/log-canonical")
def log_canonical_food_entry(
    user_id: int,
    entry: CanonicalNutritionLogRequest,
):
    if entry.entry_date is not None:
        try:
            date_cls.fromisoformat(entry.entry_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="entry_date must use YYYY-MM-DD format.",
            ) from exc

    has_grams = entry.grams is not None
    has_serving_unit = entry.serving_unit_id is not None or entry.quantity is not None
    if has_grams and has_serving_unit:
        raise HTTPException(
            status_code=400,
            detail="Provide either grams or serving_unit_id with quantity, not both.",
        )
    if not has_grams and not has_serving_unit:
        raise HTTPException(
            status_code=400,
            detail="Either grams or serving_unit_id with quantity is required.",
        )
    if has_serving_unit and (entry.serving_unit_id is None or entry.quantity is None):
        raise HTTPException(
            status_code=400,
            detail="serving_unit_id and quantity are required for serving-unit logging.",
        )

    try:
        if has_grams:
            logged_entry = add_canonical_food_entry(
                user_id=user_id,
                canonical_food_id=entry.canonical_food_id,
                grams=entry.grams,
                entry_date=entry.entry_date,
                meal_type=entry.meal_type,
                notes=entry.notes,
            )
        else:
            logged_entry = log_canonical_food_serving(
                user_id=user_id,
                canonical_food_id=entry.canonical_food_id,
                serving_unit_id=entry.serving_unit_id,
                quantity=entry.quantity,
                entry_date=entry.entry_date,
                meal_type=entry.meal_type,
                notes=entry.notes,
            )
    except CanonicalFoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ServingUnitNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitFoodMismatchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (CanonicalFoodLoggingError, ServingUnitLoggingError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        **logged_entry,
    }


@router.post("/nutrition/{user_id}/log-serving")
def log_serving_unit_food_entry(
    user_id: int,
    entry: ServingUnitNutritionLogRequest,
):
    if entry.logged_date is not None:
        try:
            date_cls.fromisoformat(entry.logged_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="logged_date must use YYYY-MM-DD format.",
            ) from exc

    try:
        logged_entry = log_canonical_food_serving(
            user_id=user_id,
            canonical_food_id=entry.canonical_food_id,
            serving_unit_id=entry.serving_unit_id,
            quantity=entry.quantity,
            entry_date=entry.logged_date,
            meal_type=entry.meal_type or entry.meal,
            notes=entry.notes,
        )
    except CanonicalFoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ServingUnitNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanonicalFoodInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServingUnitFoodMismatchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (CanonicalFoodLoggingError, ServingUnitLoggingError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": user_id,
        **logged_entry,
    }
