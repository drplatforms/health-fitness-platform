# =====================================
# Imports
# =====================================

from datetime import date as date_cls
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, BeforeValidator

from models.personal_food_models import PersonalFoodRevisionInput
from services.food_logging_recents_service import get_recent_canonical_foods
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
from services.personal_food_logging_service import (
    PersonalFoodLogEntryNotFoundError,
    delete_personal_food_entry,
    get_daily_personal_food_logs,
    log_personal_food,
    update_personal_food_entry,
)
from services.personal_food_service import (
    PersonalFoodArchivedError,
    PersonalFoodDuplicateNameError,
    PersonalFoodNotFoundError,
    PersonalFoodUserNotFoundError,
    PersonalFoodValidationError,
    archive_personal_food,
    create_personal_food,
    get_personal_food,
    list_personal_foods,
    restore_personal_food,
    revise_personal_food,
    search_personal_foods,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Request Models
# =====================================


def _reject_boolean_numeric(value: Any) -> Any:
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid numeric input.")
    return value


PersonalFoodNumber = Annotated[float, BeforeValidator(_reject_boolean_numeric)]
PersonalFoodId = Annotated[int, BeforeValidator(_reject_boolean_numeric)]


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
    serving_unit_id: int | None = None
    quantity: float | None = None
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


class PersonalFoodCreateRequest(BaseModel):
    display_name: str
    brand_name: str | None = None
    input_basis: str
    serving_name: str | None = None
    serving_grams: PersonalFoodNumber | None = None
    calories: PersonalFoodNumber | None = None
    protein_g: PersonalFoodNumber | None = None
    carbs_g: PersonalFoodNumber | None = None
    fat_g: PersonalFoodNumber | None = None
    source_note: str | None = None


class PersonalFoodRevisionRequest(BaseModel):
    display_name: str | None = None
    brand_name: str | None = None
    input_basis: str
    serving_name: str | None = None
    serving_grams: PersonalFoodNumber | None = None
    calories: PersonalFoodNumber | None = None
    protein_g: PersonalFoodNumber | None = None
    carbs_g: PersonalFoodNumber | None = None
    fat_g: PersonalFoodNumber | None = None
    source_note: str | None = None


class PersonalFoodLogRequest(BaseModel):
    personal_food_id: PersonalFoodId
    grams: PersonalFoodNumber | None = None
    serving_quantity: PersonalFoodNumber | None = None
    entry_date: str | None = None
    meal_type: str | None = None
    notes: str | None = None


class PersonalFoodLogUpdateRequest(BaseModel):
    grams: PersonalFoodNumber | None = None
    serving_quantity: PersonalFoodNumber | None = None
    meal_type: str | None = None
    entry_date: str | None = None


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
            serving_unit_id=entry.serving_unit_id,
            quantity=entry.quantity,
            meal_type=entry.meal_type,
            entry_date=entry.entry_date,
        )
    except CanonicalFoodLogEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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


@router.get("/nutrition/{user_id}/recent-canonical-foods")
def recent_canonical_foods(user_id: int, limit: str = "10"):
    return {
        "success": True,
        "user_id": user_id,
        "results": get_recent_canonical_foods(user_id=user_id, limit=limit),
    }


# =====================================
# Personal Food Endpoints
# =====================================


@router.post("/nutrition/{user_id}/personal-foods")
def create_owned_personal_food(
    user_id: int,
    request: PersonalFoodCreateRequest,
):
    try:
        personal_food = create_personal_food(
            user_id=user_id,
            revision_input=_personal_food_revision_input(request),
        )
    except PersonalFoodDuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "personal_food": personal_food.to_public_dict(),
    }


@router.get("/nutrition/{user_id}/personal-foods")
def list_owned_personal_foods(
    user_id: int,
    include_archived: bool = False,
    limit: int = 50,
):
    try:
        personal_foods = list_personal_foods(
            user_id=user_id,
            include_archived=include_archived,
            limit=limit,
        )
    except PersonalFoodUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "results": [item.to_public_dict() for item in personal_foods],
    }


@router.get("/nutrition/{user_id}/personal-foods/search")
def search_owned_personal_foods(
    user_id: int,
    q: str,
    include_archived: bool = False,
    limit: int = 20,
):
    try:
        personal_foods = search_personal_foods(
            user_id=user_id,
            query=q,
            include_archived=include_archived,
            limit=limit,
        )
    except PersonalFoodUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "results": [item.to_public_dict() for item in personal_foods],
    }


@router.get("/nutrition/{user_id}/personal-foods/{personal_food_id}")
def read_owned_personal_food(user_id: int, personal_food_id: int):
    try:
        personal_food = get_personal_food(
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "personal_food": personal_food.to_public_dict(),
    }


@router.patch("/nutrition/{user_id}/personal-foods/{personal_food_id}")
def revise_owned_personal_food(
    user_id: int,
    personal_food_id: int,
    request: PersonalFoodRevisionRequest,
):
    try:
        personal_food = revise_personal_food(
            user_id=user_id,
            personal_food_id=personal_food_id,
            revision_input=_personal_food_revision_input(request),
        )
    except PersonalFoodDuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "personal_food": personal_food.to_public_dict(),
    }


@router.delete("/nutrition/{user_id}/personal-foods/{personal_food_id}")
def archive_owned_personal_food(user_id: int, personal_food_id: int):
    try:
        personal_food = archive_personal_food(
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "personal_food": personal_food.to_public_dict(),
    }


@router.post("/nutrition/{user_id}/personal-foods/{personal_food_id}/restore")
def restore_owned_personal_food(user_id: int, personal_food_id: int):
    try:
        personal_food = restore_personal_food(
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "personal_food": personal_food.to_public_dict(),
    }


@router.post("/nutrition/{user_id}/log-personal")
def log_owned_personal_food(user_id: int, request: PersonalFoodLogRequest):
    try:
        logged = log_personal_food(
            user_id=user_id,
            personal_food_id=request.personal_food_id,
            grams=request.grams,
            serving_quantity=request.serving_quantity,
            entry_date=request.entry_date,
            meal_type=request.meal_type,
            notes=request.notes,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (PersonalFoodArchivedError, PersonalFoodValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        **logged.to_public_dict(),
    }


@router.get("/nutrition/{user_id}/personal-logs")
def daily_personal_food_logs(user_id: int, date: str):
    try:
        entries = get_daily_personal_food_logs(user_id=user_id, entry_date=date)
    except PersonalFoodUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "date": date,
        "entries": entries,
    }


@router.patch("/nutrition/{user_id}/personal-logs/{entry_id}")
def update_personal_logged_food_entry(
    user_id: int,
    entry_id: int,
    request: PersonalFoodLogUpdateRequest,
):
    try:
        updated_entry = update_personal_food_entry(
            user_id=user_id,
            entry_id=entry_id,
            grams=request.grams,
            serving_quantity=request.serving_quantity,
            meal_type=request.meal_type,
            entry_date=request.entry_date,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodLogEntryNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "entry": updated_entry,
    }


@router.delete("/nutrition/{user_id}/personal-logs/{entry_id}")
def delete_personal_logged_food_entry(
    user_id: int,
    entry_id: int,
    date: str | None = None,
):
    try:
        deleted_entry = delete_personal_food_entry(
            user_id=user_id,
            entry_id=entry_id,
            entry_date=date,
        )
    except (PersonalFoodUserNotFoundError, PersonalFoodLogEntryNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersonalFoodValidationError as exc:
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


def _personal_food_revision_input(
    request: PersonalFoodCreateRequest | PersonalFoodRevisionRequest,
) -> PersonalFoodRevisionInput:
    return PersonalFoodRevisionInput(
        display_name=request.display_name,
        brand_name=request.brand_name,
        input_basis=request.input_basis,
        serving_name=request.serving_name,
        serving_grams=request.serving_grams,
        calories=request.calories,
        protein_g=request.protein_g,
        carbs_g=request.carbs_g,
        fat_g=request.fat_g,
        source_note=request.source_note,
    )


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
