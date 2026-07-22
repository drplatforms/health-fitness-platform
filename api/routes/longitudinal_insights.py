from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from services.longitudinal_insight_service import (
    DEFAULT_MAX_INSIGHTS,
    MAX_INSIGHTS,
    build_longitudinal_insight_feed,
)

router = APIRouter()


@router.get("/insights/longitudinal/{user_id}")
def longitudinal_insights(
    user_id: int,
    as_of_date: Annotated[
        date | None,
        Query(description="Historical date to evaluate; defaults to the current date."),
    ] = None,
    target_date: Annotated[
        date | None,
        Query(deprecated=True, description="Compatibility alias for as_of_date."),
    ] = None,
    max_insights: int = Query(default=DEFAULT_MAX_INSIGHTS, ge=1, le=MAX_INSIGHTS),
):
    if as_of_date is not None and target_date is not None and as_of_date != target_date:
        raise HTTPException(
            status_code=422,
            detail="as_of_date and target_date must match when both are provided",
        )
    feed = build_longitudinal_insight_feed(
        user_id=user_id,
        as_of_date=as_of_date,
        target_date=target_date,
        max_insights=max_insights,
    )
    return {"success": True, **feed.to_dict()}
