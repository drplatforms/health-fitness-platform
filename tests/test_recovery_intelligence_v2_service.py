from __future__ import annotations

from datetime import date, timedelta

import database
from models.recovery_intelligence_v2_models import RecoveryIntelligenceV2Summary
from services.recovery_intelligence_v2_service import build_recovery_intelligence_v2


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (1, "Recovery V2 Service User", 190.0),
    )
    conn.commit()
    conn.close()


def _insert_checkin(
    *,
    user_id: int = 1,
    target_date: str,
    sleep: float | None = 7.0,
    energy: int | None = 6,
    soreness: int | None = 3,
    sleep_quality: int | None = None,
    stress: int | None = None,
    motivation: int | None = None,
    pain_concern: str | None = None,
    pain_area: str | None = None,
    weight: float | None = 190.0,
    created_at: str = "2026-06-14T08:00:00",
    notes: str | None = None,
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id,
            checkin_date,
            body_weight,
            sleep_hours,
            sleep_quality,
            energy_level,
            soreness_level,
            stress_level,
            training_motivation,
            pain_concern,
            pain_area,
            mood,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            target_date,
            weight,
            sleep,
            sleep_quality,
            energy,
            soreness,
            stress,
            motivation,
            pain_concern,
            pain_area,
            "okay",
            notes,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def _day(days_ago: int) -> str:
    return (date(2026, 6, 14) - timedelta(days=days_ago)).isoformat()


def test_service_returns_recovery_intelligence_v2_summary(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(14):
        _insert_checkin(
            target_date=_day(days_ago),
            sleep=7.2,
            energy=7,
            soreness=3,
            weight=190.0 - days_ago * 0.1,
        )

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert isinstance(summary, RecoveryIntelligenceV2Summary)
    assert summary.model_version == "recovery_intelligence_v2_service_v2"
    assert summary.source_table == "daily_checkins"
    assert summary.current_day is not None
    assert summary.windows["recent_7_days"]["checkin_days"] == 7
    assert summary.baseline is not None
    assert summary.data_quality.checkin_days == 14
    assert summary.readiness_classification in {
        "manageable",
        "supportive",
        "improving",
    }
    assert summary.recovery_pressure == "low"
    assert summary.source_facts


def test_no_checkins_returns_valid_limited_missing_summary(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.current_day is None
    assert summary.data_quality.status == "missing"
    assert summary.confidence == "Limited"
    assert summary.readiness_classification == "unknown"
    assert summary.recovery_pressure == "unknown"
    assert summary.baseline is not None
    assert summary.baseline.checkin_days == 0
    assert summary.recent_vs_baseline is not None
    assert summary.recent_vs_baseline.trend_direction == "unknown"
    assert summary.reason_codes
    assert summary.limitations
    assert "overtraining" not in summary.coach_safe_summary.lower()


def test_duplicate_same_day_checkins_collapse_by_latest_created_at_id(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(
        target_date="2026-06-14",
        sleep=5.0,
        energy=3,
        soreness=8,
        created_at="2026-06-14T06:00:00",
    )
    _insert_checkin(
        target_date="2026-06-14",
        sleep=8.0,
        energy=8,
        soreness=2,
        created_at="2026-06-14T09:00:00",
    )

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.current_day is not None
    assert summary.current_day.sleep_hours == 8.0
    assert summary.current_day.energy_level == 8.0
    assert summary.current_day.soreness_level == 2.0
    assert summary.data_quality.duplicate_days_collapsed == 1
    assert "duplicate_checkins_deduped_by_latest_created_at" in summary.reason_codes


def test_missing_values_remain_none_not_zero(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(
        target_date="2026-06-14",
        sleep=None,
        energy=None,
        soreness=None,
        weight=None,
    )

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.current_day is not None
    assert summary.current_day.sleep_hours is None
    assert summary.current_day.energy_level is None
    assert summary.current_day.soreness_level is None
    assert summary.current_day.body_weight_lb is None
    assert summary.current_day.sleep_quality is None
    assert summary.current_day.stress_level is None
    assert summary.current_day.training_motivation is None
    assert summary.current_day.pain_concern is None
    assert summary.signal_context is not None
    assert summary.signal_context.sleep_quality_context == "unknown"
    assert summary.signal_context.stress_context == "unknown"
    assert summary.signal_context.motivation_context == "unknown"
    assert summary.signal_context.pain_context == "unknown"
    assert summary.windows["recent_7_days"]["sleep_quality_value_days"] == 0
    assert summary.windows["recent_7_days"]["stress_value_days"] == 0
    assert summary.windows["recent_7_days"]["training_motivation_value_days"] == 0
    assert summary.windows["recent_7_days"]["pain_concern_value_days"] == 0
    assert summary.sleep_interpretation.current_value is None
    assert summary.sleep_interpretation.recent_average is None
    assert summary.body_weight_interpretation is not None
    assert summary.body_weight_interpretation.recent_average is None


def test_baseline_and_recent_deltas_construct_when_enough_data(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(7):
        _insert_checkin(target_date=_day(days_ago), sleep=7.5, energy=8, soreness=2)
    for days_ago in range(7, 14):
        _insert_checkin(target_date=_day(days_ago), sleep=6.5, energy=6, soreness=5)
    for days_ago in range(14, 28):
        _insert_checkin(target_date=_day(days_ago), sleep=7.0, energy=7, soreness=3)

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.baseline is not None
    assert summary.baseline.baseline_window_days == 28
    assert summary.baseline.checkin_days == 28
    assert summary.recent_vs_baseline is not None
    assert summary.recent_vs_baseline.sleep_delta is not None
    assert summary.recent_vs_baseline.trend_direction in {"improving", "stable"}
    assert summary.recent_vs_prior is not None
    assert summary.recent_vs_prior.sleep_delta == 1.0
    assert summary.recent_vs_prior.energy_delta == 2.0
    assert summary.recent_vs_prior.soreness_delta == -3.0
    assert summary.recent_vs_prior.trend_direction == "improving"


def test_data_quality_records_expected_days_missing_fields_and_limitations(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in [0, 2, 4]:
        _insert_checkin(target_date=_day(days_ago), sleep=None, energy=6, soreness=3)

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.data_quality.expected_days == 28
    assert summary.data_quality.checkin_days == 3
    assert summary.data_quality.missing_sleep_days == 28
    assert summary.data_quality.missing_energy_days == 25
    assert summary.data_quality.missing_soreness_days == 25
    assert summary.data_quality.confidence == "Limited"
    assert summary.data_quality.reason_codes
    assert summary.data_quality.limitations
    assert summary.sleep_interpretation.confidence == "Limited"
    assert summary.sleep_interpretation.reason_codes
    assert summary.sleep_interpretation.limitations


def test_source_facts_are_public_safe_and_no_raw_rows(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(target_date="2026-06-14", notes="private note")

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.source_facts
    for fact in summary.source_facts:
        assert fact.source_table == "daily_checkins"
        assert fact.field_name in {
            "checkin_date",
            "sleep_hours",
            "sleep_quality",
            "energy_level",
            "soreness_level",
            "stress_level",
            "training_motivation",
            "pain_concern",
            "body_weight",
        }
        assert "private note" not in fact.value_summary
        assert "INSERT" not in fact.value_summary.upper()


def test_forbidden_recovery_language_is_not_emitted(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for days_ago in range(7):
        _insert_checkin(target_date=_day(days_ago), sleep=5.0, energy=3, soreness=8)

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")
    public_text = " ".join(
        [
            summary.coach_safe_summary,
            *summary.reason_codes,
            *summary.limitations,
            *(fact.value_summary for fact in summary.source_facts),
        ]
    ).lower()

    forbidden = [
        "overtraining",
        "injury",
        "illness",
        "diagnosis",
        "sleep disorder",
        "must deload",
        "automatic deload",
    ]
    assert all(term not in public_text for term in forbidden)
    assert summary.recovery_pressure == "high"
    assert summary.readiness_classification == "recovery_limited"


def test_richer_signal_context_keeps_distinct_raw_and_derived_meanings(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(
        target_date="2026-06-14",
        sleep=8.0,
        sleep_quality=2,
        energy=7,
        stress=5,
        motivation=2,
        soreness=8,
        pain_concern="mild",
        pain_area="knee",
    )

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.current_day is not None
    assert summary.current_day.sleep_hours == 8.0
    assert summary.current_day.sleep_quality == 2.0
    assert summary.current_day.stress_level == 5.0
    assert summary.current_day.training_motivation == 2.0
    assert summary.current_day.soreness_level == 8.0
    assert summary.current_day.pain_concern == "mild"
    assert summary.current_day.pain_area == "knee"
    assert summary.signal_context is not None
    assert summary.signal_context.sleep_duration_context == "typical"
    assert summary.signal_context.sleep_quality_context == "poor"
    assert summary.signal_context.energy_context == "moderate"
    assert summary.signal_context.stress_context == "high"
    assert summary.signal_context.motivation_context == "low"
    assert summary.signal_context.soreness_context == "high"
    assert summary.signal_context.pain_context == "mild"
    assert summary.signal_context.pain_area == "knee"
    assert summary.windows["recent_7_days"]["average_sleep_quality"] == 2.0
    assert summary.windows["recent_7_days"]["average_stress_level"] == 5.0
    assert summary.windows["recent_7_days"]["average_training_motivation"] == 2.0
    assert summary.windows["recent_7_days"]["sleep_quality_value_days"] == 1
    assert summary.windows["recent_7_days"]["stress_value_days"] == 1
    assert summary.windows["recent_7_days"]["training_motivation_value_days"] == 1
    assert summary.windows["recent_7_days"]["pain_concern_value_days"] == 1
    assert summary.windows["recent_7_days"]["pain_concern_counts"]["mild"] == 1


def test_low_or_limited_confidence_includes_reasons_or_limitations(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(target_date="2026-06-14")

    summary = build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    assert summary.confidence in {"Limited", "Low"}
    assert summary.reason_codes or summary.limitations
    assert summary.data_quality.reason_codes or summary.data_quality.limitations


def test_service_does_not_mutate_database(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_checkin(target_date="2026-06-14")
    conn = database.get_connection()
    before = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()

    build_recovery_intelligence_v2(user_id=1, target_date="2026-06-14")

    conn = database.get_connection()
    after = conn.execute("SELECT COUNT(*) AS count FROM daily_checkins").fetchone()[
        "count"
    ]
    conn.close()
    assert after == before
