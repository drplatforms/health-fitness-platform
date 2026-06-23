from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from models.weekly_coach_summary_models import ApprovedWeeklyCoachSummary
from services.weekly_coach_summary_persistence_service import (
    WEEKLY_COACH_SUMMARY_TABLE,
    WeeklyCoachSummaryPersistenceError,
    ensure_weekly_coach_summary_schema,
    get_latest_approved_weekly_summary,
    get_weekly_summary_by_id,
    list_weekly_summaries_for_user,
    mark_weekly_summary_stale,
    save_approved_weekly_summary,
)
from services.weekly_coach_summary_service import (
    build_weekly_summary_context_from_fixture,
    generate_approved_weekly_summary,
)


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _summary(*, workouts_completed: int = 3) -> ApprovedWeeklyCoachSummary:
    context = build_weekly_summary_context_from_fixture(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        training_days_logged=max(workouts_completed, 0),
        workouts_completed=workouts_completed,
        planned_workouts=4,
        recovery_notes_available=workouts_completed > 0,
        nutrition_days_logged=3 if workouts_completed else 0,
        protein_days_logged=3 if workouts_completed else 0,
        average_energy=7 if workouts_completed else None,
        average_soreness=4 if workouts_completed else None,
    )
    return generate_approved_weekly_summary(context)


def test_schema_table_can_be_created() -> None:
    conn = _connection()

    ensure_weekly_coach_summary_schema(conn)

    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (WEEKLY_COACH_SUMMARY_TABLE,),
    ).fetchone()
    assert row is not None


def test_approved_deterministic_summary_can_be_saved_and_loaded_by_id() -> None:
    conn = _connection()
    saved = save_approved_weekly_summary(
        summary=_summary(),
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
        sanitized_metadata={
            "provider_attempted": False,
            "fallback_used": False,
            "parse_status": "not_attempted",
            "validation_status": "approved",
            "final_summary_source": "deterministic",
        },
    )

    loaded = get_weekly_summary_by_id(saved.record_id, connection=conn)

    assert loaded is not None
    assert loaded.record_id == saved.record_id
    assert loaded.approved_summary.headline == saved.headline
    assert loaded.public_safe is True
    assert loaded.displayable is True
    assert loaded.sanitized_metadata["provider_attempted"] is False


def test_latest_approved_summary_can_be_loaded_by_user_and_week() -> None:
    conn = _connection()
    first = save_approved_weekly_summary(
        summary=_summary(),
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )
    second = save_approved_weekly_summary(
        summary=_summary(),
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )

    latest = get_latest_approved_weekly_summary(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )
    stale_first = get_weekly_summary_by_id(first.record_id, connection=conn)

    assert latest is not None
    assert latest.record_id == second.record_id
    assert stale_first is not None
    assert stale_first.stale is True


def test_deterministic_fallback_summary_can_be_saved_and_loaded() -> None:
    conn = _connection()
    saved = save_approved_weekly_summary(
        summary=_summary(workouts_completed=0),
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
        sanitized_metadata={
            "provider_attempted": False,
            "fallback_used": True,
            "fallback_reason": "deterministic fallback",
            "parse_status": "not_attempted",
            "validation_status": "approved",
            "final_summary_source": "deterministic_fallback",
        },
    )

    loaded = get_weekly_summary_by_id(saved.record_id, connection=conn)

    assert loaded is not None
    assert loaded.source == "deterministic_fallback"
    assert loaded.public_safe is True
    assert loaded.displayable is True
    assert "deterministic_fallback_used" in loaded.reason_codes
    assert loaded.sanitized_metadata["fallback_used"] is True


def test_non_public_safe_summary_cannot_be_saved_as_displayable() -> None:
    conn = _connection()
    safe = _summary()
    unsafe = ApprovedWeeklyCoachSummary(
        headline=safe.headline,
        weekly_overview=safe.weekly_overview,
        recovery_observation=safe.recovery_observation,
        nutrition_observation=safe.nutrition_observation,
        training_observation=safe.training_observation,
        primary_pattern=safe.primary_pattern,
        recommended_focus=safe.recommended_focus,
        next_week_guidance=safe.next_week_guidance,
        confidence=safe.confidence,
        source=safe.source,
        public_safe=False,
        displayable=False,
        reason_codes=safe.reason_codes,
        limitations=safe.limitations,
    )

    with pytest.raises(WeeklyCoachSummaryPersistenceError):
        save_approved_weekly_summary(
            summary=unsafe,
            user_id=102,
            week_start="2026-06-15",
            week_end="2026-06-21",
            connection=conn,
        )


def test_empty_required_sections_cannot_be_saved() -> None:
    conn = _connection()
    summary = _summary()
    object.__setattr__(summary, "headline", "")

    with pytest.raises(WeeklyCoachSummaryPersistenceError):
        save_approved_weekly_summary(
            summary=summary,
            user_id=102,
            week_start="2026-06-15",
            week_end="2026-06-21",
            connection=conn,
        )


def test_raw_or_rejected_provider_metadata_is_rejected() -> None:
    conn = _connection()

    with pytest.raises(WeeklyCoachSummaryPersistenceError):
        save_approved_weekly_summary(
            summary=_summary(),
            user_id=102,
            week_start="2026-06-15",
            week_end="2026-06-21",
            connection=conn,
            sanitized_metadata={"raw_provider_output": "blocked"},
        )

    with pytest.raises(WeeklyCoachSummaryPersistenceError):
        save_approved_weekly_summary(
            summary=_summary(),
            user_id=102,
            week_start="2026-06-15",
            week_end="2026-06-21",
            connection=conn,
            sanitized_metadata={"prompt_text": "blocked"},
        )


def test_stale_and_expired_records_are_not_returned_as_latest() -> None:
    conn = _connection()
    saved = save_approved_weekly_summary(
        summary=_summary(),
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )
    assert mark_weekly_summary_stale(saved.record_id, connection=conn) is True

    latest = get_latest_approved_weekly_summary(
        user_id=102,
        week_start="2026-06-15",
        week_end="2026-06-21",
        connection=conn,
    )

    assert latest is None


def test_list_weekly_summaries_for_user_is_bounded() -> None:
    conn = _connection()
    for _ in range(3):
        save_approved_weekly_summary(
            summary=_summary(),
            user_id=102,
            week_start="2026-06-15",
            week_end="2026-06-21",
            connection=conn,
        )

    records = list_weekly_summaries_for_user(user_id=102, connection=conn, limit=2)

    assert len(records) == 2
    assert all(record.user_id == 102 for record in records)


def test_persistence_service_has_no_provider_runtime_worker_or_ui_dependency_text() -> (
    None
):
    source = (
        Path("services/weekly_coach_summary_persistence_service.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    forbidden = (
        "daily_coach_async_provider_runtime_service",
        "ollama",
        "crewai",
        "streamlit",
        "worker",
        "scheduler",
    )
    assert all(term not in source for term in forbidden)
