# =====================================
# Imports
# =====================================

from fastapi import APIRouter

from services.recovery_service import (
    get_recent_recovery_metrics,
    get_recent_recovery_reports,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


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


@router.get("/recovery/metrics")
def recovery_metrics():
    metrics = get_recent_recovery_metrics()

    return {"success": True, "metrics": metrics}
