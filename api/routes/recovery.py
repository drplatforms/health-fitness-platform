# =====================================
# Imports
# =====================================

from fastapi import APIRouter
from pydantic import BaseModel

from services.recovery_service import (
    get_recent_recovery_metrics,
    get_recent_recovery_reports,
    get_recovery_checkin,
    save_recovery_checkin,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Request Models
# =====================================


class RecoveryCheckInRequest(BaseModel):
    user_id: int
    target_date: str | None = None
    body_weight: float | None = None
    sleep_hours: float
    energy_level: int
    soreness_level: int
    mood: str | None = None
    notes: str | None = None


# =====================================
# Recovery Reports Endpoint
# =====================================


@router.get("/recovery/reports")
def recovery_reports():
    reports = get_recent_recovery_reports()

    return {"success": True, "reports": reports}


# =====================================
# Recovery Metrics Endpoint
# =====================================


@router.get("/recovery/metrics/{user_id}")
def recovery_metrics(user_id: int):
    metrics = get_recent_recovery_metrics(user_id=user_id)

    return {"success": True, "metrics": metrics}


@router.get("/recovery/checkins/{user_id}")
def recovery_checkin(user_id: int, target_date: str | None = None):
    checkin = get_recovery_checkin(user_id=user_id, target_date=target_date)

    return {"success": True, "checkin": checkin}


# =====================================
# Recovery Check-In Endpoint
# =====================================


@router.post("/recovery/checkins")
def create_recovery_checkin(checkin: RecoveryCheckInRequest):
    checkin_id = save_recovery_checkin(
        user_id=checkin.user_id,
        target_date=checkin.target_date,
        body_weight=checkin.body_weight,
        sleep_hours=checkin.sleep_hours,
        energy_level=checkin.energy_level,
        soreness_level=checkin.soreness_level,
        mood=checkin.mood,
        notes=checkin.notes,
    )

    return {
        "success": True,
        "message": "Recovery check-in saved.",
        "checkin_id": checkin_id,
    }
