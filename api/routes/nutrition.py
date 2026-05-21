# =====================================
# Imports
# =====================================

from fastapi import APIRouter

from services.nutrition_service import get_daily_nutrition

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Daily Nutrition Endpoint
# =====================================


@router.get("/nutrition/{user_id}/{date}")
def daily_nutrition(user_id: int, date: str):
    nutrition = get_daily_nutrition(user_id, date)

    if not nutrition:
        nutrition = {}

    return {"success": True, "nutrition": nutrition}
