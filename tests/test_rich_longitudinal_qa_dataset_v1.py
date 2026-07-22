from __future__ import annotations

import json
from datetime import date, timedelta

import database
from scripts.longitudinal_qa_scenario_manifest import (
    build_longitudinal_qa_scenario_manifest,
)
from scripts.seed_longitudinal_qa_data import (
    DEFAULT_DAY_COUNT,
    seed_longitudinal_qa_data,
)
from services.coach_evidence_service import build_coach_evidence_pack
from services.longitudinal_insight_service import build_longitudinal_insight_feed
from services.nutrition_trend_service import build_nutrition_trend_window

FIXED_END_DATE = date(2026, 6, 14)


def _seed(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "rich_longitudinal_v1.db")
    return seed_longitudinal_qa_data(end_date=FIXED_END_DATE)


def _rows(sql: str, params: tuple = ()) -> list[dict[str, object]]:
    conn = database.get_connection()
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _phase(
    manifest: dict[str, object], user_id: int, phase_id: str
) -> dict[str, object]:
    personas = manifest["personas"]
    assert isinstance(personas, list)
    persona = next(item for item in personas if item["user_id"] == user_id)
    return next(item for item in persona["phases"] if item["phase_id"] == phase_id)


def _seed_fingerprint() -> str:
    payload = {
        "checkins": _rows(
            """
            SELECT user_id, checkin_date, body_weight, sleep_hours, sleep_quality,
                   energy_level, soreness_level, stress_level, training_motivation,
                   pain_concern, pain_area
            FROM daily_checkins
            WHERE user_id IN (101, 102, 103, 104, 105)
            ORDER BY user_id, checkin_date
            """
        ),
        "nutrition": _rows(
            """
            SELECT fe.user_id, fe.entry_date, f.name, fe.grams
            FROM food_entries fe
            JOIN foods f ON f.id = fe.food_id
            WHERE fe.user_id IN (101, 102, 103, 104, 105)
            ORDER BY fe.user_id, fe.entry_date, fe.created_at, f.name
            """
        ),
        "training": _rows(
            """
            SELECT wes.user_id, substr(wes.completed_at, 1, 10) AS workout_date,
                   a.exercise_name, a.set_number, a.actual_reps, a.actual_weight,
                   a.actual_rir, a.completed, a.skipped
            FROM workout_execution_set_actuals a
            JOIN workout_execution_sessions wes
              ON wes.id = a.workout_execution_session_id
            WHERE wes.user_id IN (101, 102, 103, 104, 105)
            ORDER BY wes.user_id, wes.completed_at, a.exercise_name, a.set_number
            """
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def test_manifest_resolves_complete_date_relative_stories_without_product_inputs(
    tmp_path, monkeypatch
):
    _seed(tmp_path, monkeypatch)
    manifest = build_longitudinal_qa_scenario_manifest(FIXED_END_DATE)

    assert manifest["manifest_version"] == "rich_longitudinal_qa_dataset_v1"
    assert manifest["end_date"] == "2026-06-14"
    assert {item["user_id"] for item in manifest["personas"]} == {101, 103, 104}
    assert {item["user_id"] for item in manifest["controls"]} == {102, 105}

    for persona in manifest["personas"]:
        phases = persona["phases"]
        assert phases[0]["start_days_before_end"] == 364
        assert phases[-1]["end_days_before_end"] == 0
        assert phases[0]["start_date"] == "2025-06-15"
        assert phases[-1]["end_date"] == "2026-06-14"
        for earlier, later in zip(phases, phases[1:], strict=False):
            assert earlier["end_days_before_end"] == later["start_days_before_end"] + 1
        assert all(phase["intended_events"] for phase in phases)
        assert persona["profile_transitions"]
        assert all(
            transition["phase_id"] in {phase["phase_id"] for phase in phases}
            for transition in persona["profile_transitions"]
        )
        assert persona["manual_questions"]

    pack = build_coach_evidence_pack(
        user_id=104,
        question="What are the biggest changes across the last six months or year?",
        as_of_date=FIXED_END_DATE,
    )
    assert "longitudinal_qa_scenario_manifest" not in pack.source_services
    assert "manifest_version" not in json.dumps(pack.to_prompt_dict(), default=str)


def test_year_seed_is_content_deterministic_idempotent_and_user_isolated(
    tmp_path, monkeypatch
):
    first = _seed(tmp_path, monkeypatch)
    first_fingerprint = _seed_fingerprint()
    conn = database.get_connection()
    conn.execute(
        "INSERT INTO users (id, name, primary_goal) VALUES (999, 'Isolation Control', 'general_fitness')"
    )
    conn.execute(
        """
        INSERT INTO daily_checkins (
            user_id, checkin_date, sleep_hours, energy_level, soreness_level
        ) VALUES (999, '2026-06-14', 7.5, 7, 3)
        """
    )
    conn.commit()
    conn.close()

    second = seed_longitudinal_qa_data(end_date=FIXED_END_DATE)

    assert first == second
    assert _seed_fingerprint() == first_fingerprint
    assert _rows("SELECT name FROM users WHERE id = 999") == [
        {"name": "Isolation Control"}
    ]
    assert _rows("SELECT checkin_date FROM daily_checkins WHERE user_id = 999") == [
        {"checkin_date": "2026-06-14"}
    ]


def test_rich_personas_have_year_density_variation_and_factual_phase_transitions(
    tmp_path, monkeypatch
):
    seeded = _seed(tmp_path, monkeypatch)
    manifest = build_longitudinal_qa_scenario_manifest(FIXED_END_DATE)
    by_user = {item.user_id: item for item in seeded}

    assert DEFAULT_DAY_COUNT == 365
    for user_id in (101, 103, 104):
        item = by_user[user_id]
        assert 300 <= item.recovery_checkins <= 365
        assert item.nutrition_days >= 280
        assert item.completed_workouts >= 125
        coverage = _rows(
            """
            SELECT MIN(checkin_date) AS min_date, MAX(checkin_date) AS max_date,
                   COUNT(DISTINCT body_weight) AS distinct_weights,
                   COUNT(DISTINCT sleep_hours) AS distinct_sleep_values
            FROM daily_checkins WHERE user_id = ?
            """,
            (user_id,),
        )[0]
        assert coverage["min_date"] <= "2025-06-16"
        assert coverage["max_date"] == "2026-06-14"
        assert coverage["distinct_weights"] >= 8
        assert coverage["distinct_sleep_values"] >= 8

    decline = _phase(manifest, 104, "recovery_decline")
    rebound = _phase(manifest, 104, "rebound")
    recovery = _rows(
        """
        SELECT
            AVG(CASE WHEN checkin_date BETWEEN ? AND ? THEN sleep_hours END) AS decline_sleep,
            AVG(CASE WHEN checkin_date BETWEEN ? AND ? THEN sleep_hours END) AS rebound_sleep,
            AVG(CASE WHEN checkin_date BETWEEN ? AND ? THEN soreness_level END) AS decline_soreness,
            AVG(CASE WHEN checkin_date BETWEEN ? AND ? THEN soreness_level END) AS rebound_soreness
        FROM daily_checkins WHERE user_id = 104
        """,
        (
            decline["start_date"],
            decline["end_date"],
            rebound["start_date"],
            rebound["end_date"],
            decline["start_date"],
            decline["end_date"],
            rebound["start_date"],
            rebound["end_date"],
        ),
    )[0]
    assert recovery["decline_sleep"] < recovery["rebound_sleep"]
    assert recovery["decline_soreness"] > recovery["rebound_soreness"]

    weights = _rows(
        """
        SELECT checkin_date, body_weight FROM daily_checkins
        WHERE user_id = 103 AND checkin_date IN (?, ?, ?)
        ORDER BY checkin_date
        """,
        (
            (FIXED_END_DATE - timedelta(days=300)).isoformat(),
            (FIXED_END_DATE - timedelta(days=153)).isoformat(),
            FIXED_END_DATE.isoformat(),
        ),
    )
    assert len(weights) == 3
    assert weights[0]["body_weight"] > weights[1]["body_weight"]
    assert abs(weights[1]["body_weight"] - weights[2]["body_weight"]) < 2.5

    deload = _phase(manifest, 104, "deload")
    progression = _phase(manifest, 104, "progression")
    volumes = _rows(
        """
        SELECT
            AVG(CASE WHEN substr(wes.completed_at, 1, 10) BETWEEN ? AND ?
                     THEN a.actual_weight END) AS progression_weight,
            AVG(CASE WHEN substr(wes.completed_at, 1, 10) BETWEEN ? AND ?
                     THEN a.actual_weight END) AS deload_weight
        FROM workout_execution_set_actuals a
        JOIN workout_execution_sessions wes
          ON wes.id = a.workout_execution_session_id
        WHERE wes.user_id = 104 AND a.completed = 1
        """,
        (
            progression["start_date"],
            progression["end_date"],
            deload["start_date"],
            deload["end_date"],
        ),
    )[0]
    assert volumes["deload_weight"] < volumes["progression_weight"]


def test_incomplete_nutrition_uses_existing_quality_semantics_and_sparse_suppresses(
    tmp_path, monkeypatch
):
    _seed(tmp_path, monkeypatch)

    disruption_end = FIXED_END_DATE - timedelta(days=61)
    disrupted = build_nutrition_trend_window(
        user_id=103,
        end_date=disruption_end.isoformat(),
        window_days=28,
    )
    maintained = build_nutrition_trend_window(
        user_id=103,
        end_date=FIXED_END_DATE.isoformat(),
        window_days=28,
    )
    assert disrupted.intake_trend_summary.logging_consistency_status in {
        "inconsistent",
        "insufficient_data",
    }
    assert disrupted.partial_logging_day_count > 0
    assert disrupted.logged_day_count < disrupted.window_days
    assert maintained.intake_trend_summary.logging_consistency_status == "strong"
    assert maintained.complete_logging_day_count >= 21

    sparse = build_longitudinal_insight_feed(
        user_id=105,
        as_of_date=FIXED_END_DATE,
        max_insights=10,
    )
    assert sparse.insights == []


def test_structured_retrieval_covers_week_month_phase_six_month_and_year_needs(
    tmp_path, monkeypatch
):
    _seed(tmp_path, monkeypatch)

    weekly = build_coach_evidence_pack(
        user_id=104,
        question="Was my recovery worse last week than the week before?",
        as_of_date=FIXED_END_DATE - timedelta(days=14),
    )
    weekly_types = {item.evidence_type for item in weekly.evidence}
    assert "recovery_window_comparison" in weekly_types

    monthly = build_coach_evidence_pack(
        user_id=103,
        question="What changed over the last month when my weight started dropping?",
        as_of_date=FIXED_END_DATE - timedelta(days=190),
    )
    monthly_domains = {item.domain for item in monthly.evidence}
    assert {"training", "recovery", "nutrition", "body_weight"}.issubset(
        monthly_domains
    )
    assert any(
        item.evidence_type == "body_weight_trend"
        and item.structured_data["window_days"] == 28
        for item in monthly.evidence
    )

    historical = build_coach_evidence_pack(
        user_id=104,
        question="Was I progressing better three months ago on Dumbbell Bench Press?",
        as_of_date=FIXED_END_DATE,
    )
    historical_types = {item.evidence_type for item in historical.evidence}
    assert {
        "exercise_historical_progression_phase",
        "exercise_current_comparison_phase",
    }.issubset(historical_types)

    for question in (
        "When was my training going best?",
        "What patterns keep repeating?",
        "What are the biggest changes across the last six months or year?",
    ):
        pack = build_coach_evidence_pack(
            user_id=104,
            question=question,
            as_of_date=FIXED_END_DATE,
        )
        assert any(
            item.evidence_type == "training_history_overview" for item in pack.evidence
        )
        assert any(
            item.evidence_type == "longitudinal_insight" for item in pack.evidence
        )
        assert len(json.dumps(pack.to_prompt_dict(), default=str)) <= 12_000

    six_month_anchor = FIXED_END_DATE - timedelta(days=182)
    then = build_longitudinal_insight_feed(
        user_id=104,
        as_of_date=six_month_anchor,
        max_insights=10,
    )
    now = build_longitudinal_insight_feed(
        user_id=104,
        as_of_date=FIXED_END_DATE,
        max_insights=10,
    )
    assert then.insights
    assert now.insights
    assert then.to_dict() != now.to_dict()
