# =====================================
# Imports
# =====================================

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

from services.recovery_service import (
    get_recent_recovery_checkins,
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
    body_weight: float | None = Field(default=None, gt=0)
    sleep_hours: float = Field(gt=0, le=24)
    sleep_quality: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description=(
            "Self-reported sleep quality: 1 poor, 2 restless, 3 fair, "
            "4 good, 5 great."
        ),
    )
    energy_level: int = Field(ge=1, le=10)
    soreness_level: int = Field(ge=1, le=10)
    stress_level: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Self-reported stress: 1 very low through 5 very high.",
    )
    training_motivation: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description=("Self-reported desire to train: 1 very low through 5 very high."),
    )
    pain_concern: Literal["none", "mild", "significant"] | None = None
    pain_area: (
        Literal[
            "neck",
            "shoulder",
            "elbow",
            "wrist_hand",
            "upper_back",
            "lower_back",
            "hip",
            "knee",
            "ankle_foot",
            "other",
        ]
        | None
    ) = None
    mood: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_pain_context(self):
        if self.pain_area is not None and self.pain_concern not in {
            "mild",
            "significant",
        }:
            raise ValueError("pain_area requires a mild or significant pain_concern.")
        return self


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
def recovery_checkin(
    user_id: int,
    target_date: str | None = None,
    history_limit: int = 7,
):
    checkin = get_recovery_checkin(user_id=user_id, target_date=target_date)
    recent_checkins = get_recent_recovery_checkins(
        user_id=user_id,
        limit=history_limit,
    )

    return {
        "success": True,
        "checkin": checkin,
        "recent_checkins": recent_checkins,
    }


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
        sleep_quality=checkin.sleep_quality,
        energy_level=checkin.energy_level,
        soreness_level=checkin.soreness_level,
        stress_level=checkin.stress_level,
        training_motivation=checkin.training_motivation,
        pain_concern=checkin.pain_concern,
        pain_area=checkin.pain_area,
        mood=checkin.mood,
        notes=checkin.notes,
    )

    return {
        "success": True,
        "message": "Recovery check-in saved.",
        "checkin_id": checkin_id,
    }
