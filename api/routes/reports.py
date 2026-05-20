# =====================================
# Imports
# =====================================

import uuid
import threading

from fastapi import APIRouter

from services.report_service import get_latest_health_report, get_health_report_history

from services.coordinator_service import generate_health_report

# =====================================
# Router Initialization
# =====================================

router = APIRouter()
report_jobs = {}

# =====================================
# Background Report Worker
# =====================================


def run_report_job(job_id, user_id):
    try:
        report_jobs[job_id] = {"status": "running", "report": None}

        report = generate_health_report(user_id)

        report_jobs[job_id] = {"status": "completed", "report": report}

    except Exception as e:
        print("\nBACKGROUND JOB ERROR:")

        print(e)

        report_jobs[job_id] = {"status": "failed", "report": str(e)}


# =====================================
# Report Status Endpoint
# =====================================


@router.get("/reports/status/{job_id}")
def report_status(job_id: str):
    job = report_jobs.get(job_id)

    if not job:
        return {"success": False, "message": "Job not found."}

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "report": job["report"],
    }


# =====================================
# Generate AI Report Endpoint
# =====================================


@router.post("/reports/generate/{user_id}")
def generate_report(user_id: int):
    job_id = str(uuid.uuid4())

    thread = threading.Thread(target=run_report_job, args=(job_id, user_id))

    thread.start()

    return {"success": True, "job_id": job_id, "status": "running"}


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
