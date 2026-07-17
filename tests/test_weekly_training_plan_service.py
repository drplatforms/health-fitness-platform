from __future__ import annotations

from datetime import date

import pytest

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.weekly_training_plan_service import (
    WeeklyTrainingPlanNotFoundError,
    WeeklyTrainingPlanProtectedDateError,
    WeeklyTrainingPlanValidationError,
    create_weekly_training_plan,
    get_weekly_training_plan,
    get_weekly_training_plan_by_id,
    update_weekly_training_plan,
)
from services.workout_plan_persistence_service import select_current_workout_plan


def _seed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "weekly_planner.db")
    seed_qa_scenarios()


def _set_plan_date(
    plan_id: int,
    target_date: str,
    *,
    completed: bool = False,
    status: str | None = None,
) -> None:
    timestamp = f"{target_date} 09:00:00"
    effective_status = status or ("completed" if completed else "selected")
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workout_plan_instances
        SET selected_at = ?, created_at = ?, updated_at = ?,
            status = ?, completed_at = ?
        WHERE id = ?
        """,
        (
            timestamp,
            timestamp,
            timestamp,
            effective_status,
            timestamp if effective_status == "completed" else None,
            plan_id,
        ),
    )
    cursor.execute(
        """
        UPDATE workout_execution_sessions
        SET status = ?, started_at = ?, completed_at = ?, created_at = ?, updated_at = ?
        WHERE workout_plan_instance_id = ?
        """,
        (
            effective_status,
            timestamp if effective_status in {"started", "in_progress"} else None,
            timestamp if effective_status == "completed" else None,
            timestamp,
            timestamp,
            plan_id,
        ),
    )
    conn.commit()
    conn.close()


@pytest.mark.parametrize(
    ("weekdays", "expected_titles"),
    [
        ([0], ["Full Body A"]),
        ([0, 3], ["Full Body A", "Full Body B"]),
        ([0, 2, 4], ["Full Body A", "Full Body B", "Full Body C"]),
        ([0, 1, 3, 5], ["Upper A", "Lower A", "Upper B", "Lower B"]),
        (
            [0, 1, 2, 4, 5],
            ["Upper A", "Lower A", "Full Body C", "Upper B", "Lower B"],
        ),
        (
            [0, 1, 2, 3, 4, 5],
            ["Upper A", "Lower A", "Upper B", "Lower B", "Upper C", "Lower C"],
        ),
    ],
)
def test_create_persists_seven_days_and_frequency_sequence(
    tmp_path,
    monkeypatch,
    weekdays,
    expected_titles,
):
    _seed(tmp_path, monkeypatch)

    plan = create_weekly_training_plan(
        102,
        "2026-07-15",
        weekdays,
        current_date="2026-07-13",
    )

    assert plan.week_start_date == "2026-07-13"
    assert plan.week_end_date == "2026-07-19"
    assert len(plan.days) == 7
    assert [day.day_index for day in plan.days] == list(range(7))
    assert [
        day.session_title for day in plan.days if day.day_type == "training"
    ] == expected_titles
    assert all(
        day.session_directive is not None
        for day in plan.days
        if day.day_type == "training"
    )


def test_validation_rejects_zero_seven_duplicate_and_invalid_weekdays(
    tmp_path,
    monkeypatch,
):
    _seed(tmp_path, monkeypatch)

    for weekdays in ([], list(range(7)), [0, 0, 3], [-1, 2]):
        with pytest.raises(WeeklyTrainingPlanValidationError):
            create_weekly_training_plan(102, "2026-07-13", weekdays)


def test_plan_is_user_owned_for_id_reads_and_updates(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(102, "2026-07-13", [0, 2, 4])

    assert get_weekly_training_plan(101, "2026-07-13") is None
    with pytest.raises(WeeklyTrainingPlanNotFoundError):
        get_weekly_training_plan_by_id(101, plan.id)
    with pytest.raises(WeeklyTrainingPlanNotFoundError):
        update_weekly_training_plan(
            101,
            plan.id,
            [1, 3, 5],
            "standard",
            current_date="2026-07-12",
        )


def test_future_schedule_edit_recalculates_sequence(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-12",
    )

    updated = update_weekly_training_plan(
        102,
        plan.id,
        [1, 3, 5, 6],
        "extended",
        current_date="2026-07-12",
    )

    assert updated.default_workout_size_preference == "extended"
    assert [day.day_index for day in updated.days if day.day_type == "training"] == [
        1,
        3,
        5,
        6,
    ]
    assert [
        day.session_title for day in updated.days if day.day_type == "training"
    ] == [
        "Upper A",
        "Lower A",
        "Upper B",
        "Lower B",
    ]


def test_protected_edit_rejects_entire_update_without_partial_mutation(
    tmp_path,
    monkeypatch,
):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-14",
    )

    with pytest.raises(WeeklyTrainingPlanProtectedDateError):
        update_weekly_training_plan(
            102,
            plan.id,
            [1, 3, 5],
            "extended",
            current_date="2026-07-14",
        )

    unchanged = get_weekly_training_plan_by_id(
        102,
        plan.id,
        current_date="2026-07-14",
    )
    assert unchanged.default_workout_size_preference == "standard"
    assert [day.day_index for day in unchanged.days if day.day_type == "training"] == [
        0,
        2,
        4,
    ]


def test_future_edit_preserves_protected_directive_snapshots(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-16",
    )
    protected_snapshots = {
        day.day_index: day.session_directive for day in plan.days if day.is_protected
    }

    updated = update_weekly_training_plan(
        102,
        plan.id,
        [0, 2, 4, 5],
        "extended",
        current_date="2026-07-16",
    )

    assert updated.target_session_count == 4
    assert updated.default_workout_size_preference == "extended"
    assert updated.days[4].session_type == "upper_b"
    assert updated.days[5].session_type == "lower_b"
    for day_index, directive in protected_snapshots.items():
        assert updated.days[day_index].session_directive == directive


@pytest.mark.parametrize("status", ["selected", "in_progress", "completed"])
def test_persisted_future_workout_date_is_protected(tmp_path, monkeypatch, status):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-13",
    )
    selected = select_current_workout_plan(102)
    _set_plan_date(
        selected["workout_plan_instance"].id,
        "2026-07-17",
        status=status,
    )

    with pytest.raises(WeeklyTrainingPlanProtectedDateError):
        update_weekly_training_plan(
            102,
            plan.id,
            [0, 2, 5],
            "standard",
            current_date="2026-07-13",
        )


def test_missed_and_extra_workout_statuses_are_derived_without_rescheduling(
    tmp_path,
    monkeypatch,
):
    _seed(tmp_path, monkeypatch)
    plan = create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-15",
    )
    completed = select_current_workout_plan(102)
    _set_plan_date(
        completed["workout_plan_instance"].id,
        "2026-07-14",
        completed=True,
    )

    refreshed = get_weekly_training_plan_by_id(
        102,
        plan.id,
        current_date=date(2026, 7, 15),
    )
    monday = refreshed.days[0]
    tuesday = refreshed.days[1]
    wednesday = refreshed.days[2]

    assert monday.derived_status == "missed"
    assert tuesday.day_type == "rest"
    assert tuesday.derived_status == "extra_workout"
    assert wednesday.session_title == "Full Body B"
