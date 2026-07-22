from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta

import database
from models.longitudinal_insight_models import LongitudinalInsightFeed
from scripts.seed_longitudinal_qa_data import (
    longitudinal_insight_qa_dates,
    seed_longitudinal_qa_data,
)
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.longitudinal_insight_service import build_longitudinal_insight_feed
from services.nutrition_service import add_canonical_food_entry
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)
from services.workout_progression_decision_service import (
    CurrentExercisePrescription,
    build_exercise_progression_decision,
)

TARGET = date(2026, 7, 20)


def _seed_database(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_insights.db")
    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO users (
            id, name, age, gender, height_cm, starting_weight, goal_weight,
            activity_level, primary_goal
        )
        VALUES (?, ?, 35, 'male', 178, 180, 180, 'moderate',
                'strength_and_recomposition')
        """,
        [(1, "Insight User"), (2, "Other Insight User")],
    )
    cursor.execute(
        """
        UPDATE users
        SET age = 35,
            gender = 'male',
            height_cm = 178,
            starting_weight = 180,
            goal_weight = 180,
            activity_level = 'moderate',
            primary_goal = 'strength_and_recomposition'
        WHERE id IN (1, 2)
        """
    )
    conn.commit()
    conn.close()


def _insert_checkin(
    *,
    user_id: int = 1,
    days_ago: int,
    sleep: float,
    energy: int,
    soreness: int,
    sleep_quality: int = 3,
    stress: int = 3,
    motivation: int = 3,
    weight: float | None = None,
    pain_concern: str | None = "none",
    pain_area: str | None = None,
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id, checkin_date, body_weight, sleep_hours, sleep_quality,
            energy_level, soreness_level, stress_level, training_motivation,
            pain_concern, pain_area
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            (TARGET - timedelta(days=days_ago)).isoformat(),
            weight,
            sleep,
            sleep_quality,
            energy,
            soreness,
            stress,
            motivation,
            pain_concern,
            pain_area,
        ),
    )
    conn.commit()
    conn.close()


def _insert_recovery_arc(
    *, user_id: int = 1, worsening: bool = True, anchor_days_ago: int = 0
) -> None:
    for days_ago in range(anchor_days_ago + 7, anchor_days_ago + 14):
        _insert_checkin(
            user_id=user_id,
            days_ago=days_ago,
            sleep=8.0 if worsening else 6.0,
            sleep_quality=4 if worsening else 2,
            energy=8 if worsening else 5,
            soreness=2 if worsening else 7,
            stress=2 if worsening else 4,
            motivation=4 if worsening else 2,
        )
    for days_ago in range(anchor_days_ago, anchor_days_ago + 7):
        _insert_checkin(
            user_id=user_id,
            days_ago=days_ago,
            sleep=6.0 if worsening else 8.0,
            sleep_quality=2 if worsening else 4,
            energy=5 if worsening else 8,
            soreness=7 if worsening else 2,
            stress=4 if worsening else 2,
            motivation=2 if worsening else 4,
        )


def _insert_training_exposure(
    *,
    days_ago: int,
    weight: float,
    rir: int,
    reps: int = 10,
    user_id: int = 1,
    exercise_name: str = "Bench Press",
) -> None:
    performed_at = f"{(TARGET - timedelta(days=days_ago)).isoformat()}T18:00:00"
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at, completed_at
        )
        VALUES (?, 'completed', 'insight_test', 'High', 'Insight Session',
                ?, ?, ?)
        """,
        (user_id, json.dumps({"title": "Insight Session"}), performed_at, performed_at),
    )
    plan_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO planned_workout_exercises (
            workout_plan_instance_id, exercise_order, name, sets, reps_min,
            reps_max, rir_min, rir_max, notes, equipment_required_json
        )
        VALUES (?, 1, ?, 3, 8, 12, 1, 3, '', '[]')
        """,
        (plan_id, exercise_name),
    )
    planned_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id, user_id, status, started_at, completed_at
        )
        VALUES (?, ?, 'completed', ?, ?)
        """,
        (plan_id, user_id, performed_at, performed_at),
    )
    execution_id = int(cursor.lastrowid)
    for set_number in range(1, 4):
        cursor.execute(
            """
            INSERT INTO workout_execution_set_actuals (
                workout_execution_session_id, planned_workout_exercise_id,
                exercise_name, set_number, planned_reps_min, planned_reps_max,
                planned_rir_min, planned_rir_max, actual_reps, actual_weight,
                actual_rir, completed, skipped
            )
            VALUES (?, ?, ?, ?, 8, 12, 1, 3, ?, ?, ?, 1, 0)
            """,
            (execution_id, planned_id, exercise_name, set_number, reps, weight, rir),
        )
    conn.commit()
    conn.close()


def _canonical_id(query: str) -> int:
    matches = search_canonical_foods(query, limit=1)
    assert matches
    return int(matches[0].canonical_food.id)


def _log_complete_day(user_id: int, target_date: str) -> None:
    add_canonical_food_entry(user_id, _canonical_id("chicken breast"), 150, target_date)
    add_canonical_food_entry(user_id, _canonical_id("rice"), 200, target_date)
    add_canonical_food_entry(user_id, _canonical_id("olive oil"), 10, target_date)


def _clear_user_history(user_id: int = 1) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id FROM workout_execution_sessions WHERE user_id = ?
        )
        """,
        (user_id,),
    )
    cursor.execute(
        "DELETE FROM workout_execution_sessions WHERE user_id = ?", (user_id,)
    )
    cursor.execute(
        """
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id = ?
        )
        """,
        (user_id,),
    )
    cursor.execute("DELETE FROM workout_plan_instances WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM food_entries WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def _set_checkin_weight(*, days_ago: int, weight: float, user_id: int = 1) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE daily_checkins
        SET body_weight = ?
        WHERE user_id = ? AND checkin_date = ?
        """,
        (weight, user_id, (TARGET - timedelta(days=days_ago)).isoformat()),
    )
    conn.commit()
    conn.close()


def _insight_types(feed: LongitudinalInsightFeed) -> set[str]:
    return {insight.insight_type for insight in feed.insights}


def test_meaningful_recovery_change_is_detected_and_small_changes_are_deduped(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    _insert_recovery_arc(worsening=True)

    feed = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )

    recovery_insights = [item for item in feed.insights if item.domain == "recovery"]
    assert (
        len([item for item in recovery_insights if item.direction == "worsening"]) == 1
    )
    insight = recovery_insights[0]
    assert insight.insight_type == "elevated_soreness"
    assert insight.evidence_strength == "strong"
    assert insight.data_coverage.status == "strong"
    assert insight.observation_window.observation_count == 7
    assert insight.comparison_window is not None
    assert insight.comparison_window.observation_count == 7


def test_training_progression_effort_and_plateau_observations_reuse_comparable_history(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    for days_ago, weight in [(13, 100), (10, 100), (5, 110), (1, 110)]:
        _insert_training_exposure(days_ago=days_ago, weight=weight, rir=2)

    current = CurrentExercisePrescription(
        exercise_name="Bench Press",
        catalog_exercise_id=None,
        sets=3,
        reps_min=8,
        reps_max=12,
        rir_min=1,
        rir_max=3,
    )
    decision_before = asdict(
        build_exercise_progression_decision(user_id=1, current_exercise=current)
    )
    progression = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )
    decision_after = asdict(
        build_exercise_progression_decision(user_id=1, current_exercise=current)
    )

    assert "clear_progression" in _insight_types(progression)
    assert decision_after == decision_before

    _clear_user_history()
    for days_ago, rir in [(13, 3), (10, 3), (5, 1), (1, 1)]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=rir)
    effort = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )
    assert "stable_load_rising_effort" in _insight_types(effort)

    _clear_user_history()
    for days_ago in [22, 17, 13, 9, 5, 1]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=2)
    plateau = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )
    assert "performance_plateau" in _insight_types(plateau)


def test_sparse_data_and_incomplete_nutrition_are_suppressed_and_users_are_isolated(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    for days_ago in [1, 4, 8]:
        _insert_checkin(
            days_ago=days_ago,
            sleep=5,
            energy=3,
            soreness=8,
            pain_concern="mild",
            pain_area="knee",
        )
        _log_complete_day(1, (TARGET - timedelta(days=days_ago)).isoformat())

    user_one = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )
    user_two = build_longitudinal_insight_feed(
        user_id=2, target_date=TARGET, max_insights=10
    )

    assert user_one.insights == []
    assert user_two.insights == []
    assert user_one.user_id == 1
    assert user_two.user_id == 2


def test_historical_as_of_excludes_future_data_across_all_insight_families(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    historical_anchor = TARGET - timedelta(days=30)
    _insert_recovery_arc(worsening=True, anchor_days_ago=30)
    _insert_checkin(
        days_ago=45,
        sleep=8,
        energy=8,
        soreness=2,
        weight=180,
    )
    for index, days_ago in enumerate(range(43, 29, -1), start=1):
        _set_checkin_weight(days_ago=days_ago, weight=180 + index * 0.2)
    for days_ago, rir in [(43, 3), (40, 3), (35, 1), (31, 1)]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=rir)
    for days_ago, weight in [(43, 80), (40, 80), (35, 90), (31, 90)]:
        _insert_training_exposure(
            days_ago=days_ago,
            weight=weight,
            rir=2,
            exercise_name="Barbell Row",
        )
    for days_ago in range(30, 42):
        _log_complete_day(1, (TARGET - timedelta(days=days_ago)).isoformat())

    anchored_before = build_longitudinal_insight_feed(
        user_id=1, as_of_date=historical_anchor, max_insights=10
    ).to_dict()
    assert {item["domain"] for item in anchored_before["insights"]} >= {
        "recovery",
        "training",
        "nutrition",
        "body_weight",
        "cross_domain",
    }

    _insert_recovery_arc(worsening=True)
    _insert_checkin(
        days_ago=27,
        sleep=8,
        energy=8,
        soreness=2,
        weight=185,
    )
    for index, days_ago in enumerate([13, 10, 7, 4, 2, 1, 0], start=1):
        _set_checkin_weight(days_ago=days_ago, weight=185 + index * 0.2)
    for index, days_ago in enumerate([26, 23, 20, 17, 14]):
        _insert_checkin(
            days_ago=days_ago,
            sleep=8,
            energy=8,
            soreness=2,
            weight=185 + index * 0.1,
        )
    for days_ago, rir in [(13, 3), (10, 3), (5, 1), (1, 1)]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=rir)
    for days_ago, weight in [(13, 80), (10, 80), (5, 90), (1, 90)]:
        _insert_training_exposure(
            days_ago=days_ago,
            weight=weight,
            rir=2,
            exercise_name="Barbell Row",
        )
    for days_ago in range(12):
        _log_complete_day(1, (TARGET - timedelta(days=days_ago)).isoformat())

    latest = build_longitudinal_insight_feed(
        user_id=1, as_of_date=TARGET, max_insights=10
    )
    assert {item.domain for item in latest.insights} >= {
        "recovery",
        "training",
        "nutrition",
        "body_weight",
        "cross_domain",
    }

    anchored_after = build_longitudinal_insight_feed(
        user_id=1, as_of_date=historical_anchor, max_insights=10
    ).to_dict()
    assert anchored_after == anchored_before
    assert anchored_after["as_of_date"] == historical_anchor.isoformat()
    assert anchored_after["target_date"] == historical_anchor.isoformat()


def test_nutrition_logging_quality_and_body_weight_thresholds_gate_insights(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    for days_ago in range(12):
        _log_complete_day(1, (TARGET - timedelta(days=days_ago)).isoformat())
    for index, days_ago in enumerate([27, 24, 21, 18, 15, 12, 9, 6, 4, 2, 1, 0]):
        _insert_checkin(
            days_ago=days_ago,
            sleep=7.5,
            energy=7,
            soreness=3,
            weight=180 + index * 0.3,
        )

    feed = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )

    assert "sustained_nutrition_logging" in _insight_types(feed)
    weight_insight = next(
        item for item in feed.insights if item.domain == "body_weight"
    )
    assert weight_insight.direction == "increasing"
    assert weight_insight.data_coverage.status == "strong"


def test_cross_domain_association_replaces_duplicate_training_card_and_is_cautious(
    tmp_path, monkeypatch
) -> None:
    _seed_database(tmp_path, monkeypatch)
    _insert_recovery_arc(worsening=True)
    for days_ago, rir in [(13, 3), (10, 3), (5, 1), (1, 1)]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=rir)

    feed = build_longitudinal_insight_feed(
        user_id=1, target_date=TARGET, max_insights=10
    )

    cross_domain = next(item for item in feed.insights if item.domain == "cross_domain")
    assert cross_domain.insight_type == "rising_effort_with_poorer_recovery"
    assert "association, not proof of cause" in cross_domain.explanation
    assert "stable_load_rising_effort" not in _insight_types(feed)
    assert cross_domain.data_coverage.limitations == [
        "Coincident patterns do not establish causation."
    ]


def test_ranking_and_repeatability_are_deterministic(tmp_path, monkeypatch) -> None:
    _seed_database(tmp_path, monkeypatch)
    _insert_recovery_arc(worsening=True)
    for days_ago, rir in [(13, 3), (10, 3), (5, 1), (1, 1)]:
        _insert_training_exposure(days_ago=days_ago, weight=100, rir=rir)

    first = build_longitudinal_insight_feed(
        user_id=1, as_of_date=TARGET, max_insights=2
    ).to_dict()
    second = build_longitudinal_insight_feed(
        user_id=1, as_of_date=TARGET, max_insights=2
    ).to_dict()

    assert first == second
    assert len(first["insights"]) == 2
    assert first["insights"][0]["domain"] == "cross_domain"
    assert len({item["stable_id"] for item in first["insights"]}) == 2


def test_seeded_recovery_story_changes_from_deterioration_to_rebound(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_personas.db")
    seed_longitudinal_qa_data(end_date=TARGET)
    anchors = longitudinal_insight_qa_dates(TARGET)

    deterioration = build_longitudinal_insight_feed(
        user_id=104,
        as_of_date=anchors["recovery_deterioration"],
        max_insights=10,
    )
    rebound = build_longitudinal_insight_feed(
        user_id=104,
        as_of_date=anchors["recovery_rebound"],
        max_insights=10,
    )

    assert any(
        item.domain == "recovery" and item.direction == "worsening"
        for item in deterioration.insights
    )
    assert "rising_effort_with_poorer_recovery" in _insight_types(deterioration)
    assert "recovery_rebound" in _insight_types(rebound)
    assert deterioration.to_dict() != rebound.to_dict()


def test_seeded_training_story_changes_from_progression_to_rising_effort(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_personas.db")
    seed_longitudinal_qa_data(end_date=TARGET)
    anchors = longitudinal_insight_qa_dates(TARGET)

    progression = build_longitudinal_insight_feed(
        user_id=102,
        as_of_date=anchors["training_progression"],
        max_insights=10,
    )
    rising_effort = build_longitudinal_insight_feed(
        user_id=102,
        as_of_date=anchors["training_rising_effort"],
        max_insights=10,
    )

    assert "clear_progression" in _insight_types(progression)
    assert "stable_load_rising_effort" in _insight_types(rising_effort)
    assert "clear_progression" not in _insight_types(rising_effort)


def test_seeded_sparse_control_suppresses_unsupported_insights(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_personas.db")
    seed_longitudinal_qa_data(end_date=TARGET)
    sparse = build_longitudinal_insight_feed(
        user_id=105,
        as_of_date=longitudinal_insight_qa_dates(TARGET)["sparse_data_control"],
        max_insights=10,
    )

    assert sparse.insights == []


def test_default_as_of_date_uses_current_date(tmp_path, monkeypatch) -> None:
    _seed_database(tmp_path, monkeypatch)

    feed = build_longitudinal_insight_feed(user_id=1)

    assert feed.as_of_date == date.today().isoformat()
    assert feed.target_date == feed.as_of_date


def test_existing_longitudinal_qa_personas_remain_bounded(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_personas.db")
    seed_longitudinal_qa_data(end_date=TARGET)

    recovery_limited = build_longitudinal_insight_feed(
        user_id=101, as_of_date=TARGET, max_insights=5
    )
    aligned = build_longitudinal_insight_feed(
        user_id=102, as_of_date=TARGET, max_insights=5
    )
    data_quality_limited = build_longitudinal_insight_feed(
        user_id=105, as_of_date=TARGET, max_insights=5
    )

    assert "elevated_soreness" in _insight_types(recovery_limited)
    assert "sustained_nutrition_logging" in _insight_types(aligned)
    assert data_quality_limited.insights == []
    assert all(
        len(feed.insights) <= 5
        for feed in [recovery_limited, aligned, data_quality_limited]
    )
