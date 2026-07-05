from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.daily_driver_today_service import build_daily_driver_today_response

router = APIRouter()


@router.get("/api/today")
def daily_driver_today(user_id: int, date: str | None = None):
    try:
        response = build_daily_driver_today_response(user_id=user_id, target_date=date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return response.to_dict()
