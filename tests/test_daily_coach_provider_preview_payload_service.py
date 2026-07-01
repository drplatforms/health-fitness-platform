from __future__ import annotations

import inspect
import json

import database
from models.daily_coach_provider_preview_payload_models import (
    DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION,
    FORBIDDEN_PROVIDER_PREVIEW_PAYLOAD_KEYS,
)
from services import daily_coach_provider_preview_payload_service as payload_service
from services.daily_coach_intelligence_snapshot_service import (
    build_daily_coach_intelligence_snapshot,
)
from services.daily_coach_provider_preview_payload_service import (
    build_daily_coach_provider_preview_raw_data_payload,
    build_daily_coach_provider_preview_raw_data_payload_from_snapshot,
)


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
        (1, "Provider Preview Test User", 190.0),
    )
    for checkin_date, sleep, energy, soreness in [
        ("2026-06-12", 7.0, 6, 3),
        ("2026-06-13", 7.5, 7, 2),
        ("2026-06-14", 7.0, 6, 3),
    ]:
        cursor.execute(
            """
            INSERT INTO daily_checkins (
                user_id,
                checkin_date,
                body_weight,
                sleep_hours,
                energy_level,
                soreness_level
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, checkin_date, 190.0, sleep, energy, soreness),
        )
    conn.commit()
    conn.close()


def _row_counts() -> dict[str, int]:
    conn = database.get_connection()
    cursor = conn.cursor()
    counts = {
        "users": cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "daily_checkins": cursor.execute(
            "SELECT COUNT(*) FROM daily_checkins"
        ).fetchone()[0],
    }
    conn.close()
    return counts


def _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch) -> dict:
    _seed_test_db(tmp_path, monkeypatch)
    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1,
        target_date="2026-06-14",
    ).to_dict()
    snapshot["workout_set_intelligence"] = {
        "completed_execution_count": 2,
        "overall_completion_indicator": "mostly_completed",
        "overall_effort_indicator": "as_planned",
        "confidence": "Moderate",
        "source_facts": ["2 completed planned workout executions"],
    }
    snapshot["training_execution_summary"] = {
        "completed_execution_count": 2,
        "confidence": "Moderate",
    }
    snapshot["nutrition_trend_window"] = {
        "logged_day_count": 4,
        "confidence": "Low",
        "reason_codes": ["partial_logging"],
    }
    snapshot["source_services"] = [
        *snapshot["source_services"],
        "workout_set_intelligence_service",
        "training_execution_summary_service",
        "nutrition_trend_service",
    ]
    snapshot["data_completeness"] = {
        **snapshot["data_completeness"],
        "workout_set_intelligence": "usable",
        "training_execution_summary": "usable",
        "nutrition_trend_window": "usable",
    }
    snapshot["source_data_gaps"] = ["food_knowledge_expansion: pending"]
    snapshot["reason_codes"] = ["food_knowledge_expansion_pending"]
    snapshot["limitations"] = ["Food knowledge expansion is pending."]
    return snapshot


def test_payload_builds_from_daily_coach_intelligence_snapshot_object(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1,
        target_date="2026-06-14",
    )

    payload = build_daily_coach_provider_preview_raw_data_payload(snapshot)
    data = payload.to_dict()

    assert (
        data["payload_version"] == DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION
    )
    assert data["user_id"] == 1
    assert data["target_date"] == "2026-06-14"
    assert data["source_snapshot_version"] == snapshot.snapshot_version
    assert data["source_services"] == snapshot.source_services
    assert (
        data["source_data"]["recovery_intelligence"]
        == snapshot.recovery_intelligence.to_dict()
    )
    assert (
        data["source_data"]["foundation_layer_status"]
        == snapshot.foundation_layer_status
    )


def test_payload_builds_from_serialized_snapshot_dict_and_preserves_raw_sections(
    tmp_path, monkeypatch
) -> None:
    snapshot_dict = _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch)

    payload = build_daily_coach_provider_preview_raw_data_payload_from_snapshot(
        snapshot_dict
    )
    data = payload.to_dict()
    source_data = data["source_data"]

    assert (
        source_data["recovery_intelligence"] == snapshot_dict["recovery_intelligence"]
    )
    assert (
        source_data["recovery_intelligence_v2"]
        == snapshot_dict["recovery_intelligence_v2"]
    )
    assert (
        source_data["workout_set_intelligence"]
        == snapshot_dict["workout_set_intelligence"]
    )
    assert (
        source_data["training_execution_summary"]
        == snapshot_dict["training_execution_summary"]
    )
    assert (
        source_data["nutrition_trend_window"] == snapshot_dict["nutrition_trend_window"]
    )
    assert (
        source_data["foundation_layer_status"]
        == snapshot_dict["foundation_layer_status"]
    )
    assert source_data["data_completeness"] == snapshot_dict["data_completeness"]
    assert source_data["source_data_gaps"] == snapshot_dict["source_data_gaps"]
    assert source_data["reason_codes"] == snapshot_dict["reason_codes"]
    assert source_data["limitations"] == snapshot_dict["limitations"]


def test_payload_marks_developer_preview_and_blocks_runtime_authority(
    tmp_path, monkeypatch
) -> None:
    snapshot_dict = _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch)

    data = build_daily_coach_provider_preview_raw_data_payload(snapshot_dict).to_dict()

    assert data["developer_preview_only"] is True
    assert data["provider_call_allowed"] is False
    assert data["persistence_allowed"] is False
    assert data["product_surface_allowed"] is False
    assert data["backend_truth_contract"]["backend_owns_facts"] is True
    assert data["backend_truth_contract"]["provider_output_is_not_truth"] is True
    assert (
        data["backend_truth_contract"][
            "provider_output_may_not_change_daily_next_action"
        ]
        is True
    )
    assert "change Daily Next Action selection" in data["forbidden_provider_authority"]
    assert "write to database" in data["forbidden_provider_authority"]
    assert "invent facts" in data["forbidden_provider_authority"]


def test_provider_voice_space_rejects_sentence_bank_and_pre_caged_voice(
    tmp_path, monkeypatch
) -> None:
    snapshot_dict = _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch)

    data = build_daily_coach_provider_preview_raw_data_payload(snapshot_dict).to_dict()
    voice_space = data["provider_voice_space"]
    guidance = data["provider_input_guidance"]

    assert voice_space["voice_goal"] == "natural_coaching_language_from_backend_facts"
    assert voice_space["do_not_force_sentence_bank"] is True
    assert voice_space["do_not_reduce_input_to_backend_prose_summary"] is True
    assert voice_space["allow_varied_sentence_structure"] is True
    assert guidance["sentence_bank_authorized"] is False
    assert guidance["final_copy_authorized"] is False


def test_payload_does_not_include_final_copy_or_sentence_template_fields(
    tmp_path, monkeypatch
) -> None:
    snapshot_dict = _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch)

    data = build_daily_coach_provider_preview_raw_data_payload(snapshot_dict).to_dict()

    for forbidden_key in FORBIDDEN_PROVIDER_PREVIEW_PAYLOAD_KEYS:
        assert forbidden_key not in data
        assert forbidden_key not in data["source_data"]


def test_payload_serializes_cleanly_through_to_dict(tmp_path, monkeypatch) -> None:
    snapshot_dict = _snapshot_dict_with_all_optional_sections(tmp_path, monkeypatch)

    payload = build_daily_coach_provider_preview_raw_data_payload(snapshot_dict)
    serialized = json.dumps(payload.to_dict(), sort_keys=True)

    assert "daily_coach_provider_preview_raw_data_payload_v1" in serialized
    assert "recovery_intelligence" in serialized
    assert "provider_call_allowed" in serialized


def test_service_does_not_import_provider_runtime_modules() -> None:
    source = inspect.getsource(payload_service).lower()

    assert "crewai" not in source
    assert "openai" not in source
    assert "ollama" not in source
    assert "provider_service" not in source


def test_service_does_not_mutate_database_when_building_from_snapshot(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=1,
        target_date="2026-06-14",
    )
    before = _row_counts()

    build_daily_coach_provider_preview_raw_data_payload(snapshot)

    assert _row_counts() == before
