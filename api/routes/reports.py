# =====================================
# Imports
# =====================================

from fastapi import APIRouter

from services.report_service import get_latest_health_report, get_health_report_history

from services.coordinator_service import generate_health_report

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Generate AI Report Endpoint
# =====================================


@router.post("/reports/generate/{user_id}")
def generate_report(user_id: int):

    report = generate_health_report(user_id)

    return {"success": True, "report": report}


# =====================================
# Latest AI Report Endpoint
# =====================================


@router.get("/reports/latest/{user_id}")
def latest_report(user_id: int):

    report = get_latest_health_report(user_id)

    if report:

        return {"success": True, "report": dict(report)}

    return {"success": False, "message": "No report found"}


# =====================================
# AI Report History Endpoint
# =====================================


@router.get("/reports/history/{user_id}")
def report_history(user_id: int):

    reports = get_health_report_history(user_id=user_id, limit=5)

    return {"success": True, "reports": [dict(report) for report in reports]}
