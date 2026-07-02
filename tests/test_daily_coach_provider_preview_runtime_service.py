from __future__ import annotations

import inspect
import json

import database
from models.daily_coach_provider_preview_payload_models import (
    DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION,
    DailyCoachProviderPreviewRawDataPayload,
)
from models.daily_coach_provider_preview_runtime_models import (
    DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_RESULT_VERSION,
)
from services import daily_coach_provider_preview_runtime_service as runtime_service
from services.daily_coach_provider_preview_runtime_service import (
    build_daily_coach_provider_preview_free_voice_input,
    call_ollama_provider_preview_free_voice,
    run_daily_coach_provider_preview_runtime_spike,
)


def _payload() -> DailyCoachProviderPreviewRawDataPayload:
    return DailyCoachProviderPreviewRawDataPayload(
        payload_version=DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION,
        user_id=102,
        target_date="2026-06-14",
        generated_at="2026-06-14T12:00:00+00:00",
        developer_preview_only=True,
        provider_call_allowed=False,
        persistence_allowed=False,
        product_surface_allowed=False,
        source_snapshot_version="daily_coach_intelligence_snapshot_v1",
        source_services=["daily_coach_intelligence_snapshot_service"],
        source_data={
            "recovery_intelligence": {
                "status": "usable",
                "sleep_hours": 7.5,
                "energy_level": 7,
                "soreness_level": 2,
            },
            "training_execution_summary": {
                "completed_execution_count": 3,
                "confidence": "Moderate",
            },
            "nutrition_trend_window": {
                "logged_day_count": 5,
                "confidence": "Moderate",
            },
            "foundation_layer_status": {"status": "available"},
            "data_completeness": {"daily_coach_intelligence": "usable"},
            "source_data_gaps": [],
            "reason_codes": ["developer_preview_fixture"],
            "limitations": ["Runtime spike output is not product copy."],
        },
        data_completeness={"daily_coach_intelligence": "usable"},
        reason_codes=["developer_preview_fixture"],
        limitations=["Runtime spike output is not product copy."],
        backend_truth_contract={
            "backend_owns_facts": True,
            "provider_output_is_not_truth": True,
            "provider_output_may_not_mutate_state": True,
        },
        provider_voice_space={
            "allow_varied_sentence_structure": True,
            "developer_preview_only": True,
        },
        provider_input_guidance={
            "final_copy_authorized": False,
            "normal_today_surface_authorized": False,
        },
        forbidden_provider_authority=[
            "write to database",
            "change Daily Next Action selection",
            "invent facts",
        ],
    )


def test_free_voice_input_includes_raw_provider_preview_payload_json() -> None:
    payload = _payload()

    provider_input = build_daily_coach_provider_preview_free_voice_input(payload)

    assert "RAW_BACKEND_PAYLOAD_JSON:" in provider_input
    assert json.dumps(payload.to_dict(), indent=2, sort_keys=True) in provider_input
    assert (
        '"payload_version": "daily_coach_provider_preview_raw_data_payload_v1"'
        in provider_input
    )
    assert '"source_data"' in provider_input
    assert '"recovery_intelligence"' in provider_input
    assert '"training_execution_summary"' in provider_input
    assert '"nutrition_trend_window"' in provider_input


def test_free_voice_input_includes_minimal_authority_boundaries() -> None:
    provider_input = build_daily_coach_provider_preview_free_voice_input(_payload())

    assert (
        "Use the raw backend data below as your only source of facts" in provider_input
    )
    assert "Speak naturally and directly to the user" in provider_input
    assert "You may vary structure and phrasing" in provider_input
    assert "Do not claim to change the app" in provider_input
    assert "Do not invent facts" in provider_input
    assert "This is not product output" in provider_input


def test_free_voice_input_does_not_introduce_old_caged_prompt_shape() -> None:
    provider_input = build_daily_coach_provider_preview_free_voice_input(_payload())

    forbidden_fragments = [
        "GOOD_STYLE_EXAMPLES",
        "BAD_STYLE_EXAMPLES",
        "EXAMPLE SHAPE ONLY",
        "FOCUS_TO_COPY_EXACTLY",
        "FACT_STRINGS_FOR_USED_FACTS",
        "DAILY_COACH_NARRATIVE_JSON_SCHEMA",
        "coach_note",
        "key_takeaway",
        "recommended_focus",
        "confidence_language",
        "used_approved_facts",
        "avoided_claims",
        "Sentence 1:",
        "Sentence 2:",
        "Final sentence:",
        "Return exactly these six keys",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in provider_input


def test_runtime_result_preserves_raw_model_output_without_parsing() -> None:
    raw_model_output = (
        '{"unexpected": "shape", "coach_note": "This is intentionally raw."}'
    )

    def fake_provider(
        model_name: str,
        provider_input: str,
        timeout_seconds: float,
        ollama_base_url: str,
        temperature: float,
    ) -> str:
        assert model_name == "qwen2.5:3b"
        assert "RAW_BACKEND_PAYLOAD_JSON" in provider_input
        assert timeout_seconds == 300.0
        assert ollama_base_url == "http://localhost:11434"
        assert temperature == 0.9
        return raw_model_output

    result = run_daily_coach_provider_preview_runtime_spike(
        payload=_payload(),
        model_name="qwen2.5:3b",
        provider_callable=fake_provider,
    )

    data = result.to_dict()
    assert (
        data["result_version"]
        == DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_RESULT_VERSION
    )
    assert data["raw_model_output"] == raw_model_output
    assert data["error_type"] is None
    assert data["error_message"] is None
    assert data["developer_preview_only"] is True
    assert data["provider_call_was_opt_in"] is True
    assert data["persistence_allowed"] is False
    assert data["product_surface_allowed"] is False
    assert data["normal_today_surface_allowed"] is False
    assert result.succeeded is True


def test_runtime_result_returns_error_metadata_on_provider_failure() -> None:
    def broken_provider(
        model_name: str,
        provider_input: str,
        timeout_seconds: float,
        ollama_base_url: str,
        temperature: float,
    ) -> str:
        raise TimeoutError("provider pasture gate timed out")

    result = run_daily_coach_provider_preview_runtime_spike(
        payload=_payload(),
        model_name="qwen2.5:3b",
        provider_callable=broken_provider,
    )

    data = result.to_dict()
    assert data["raw_model_output"] is None
    assert data["error_type"] == "TimeoutError"
    assert data["error_message"] == "provider pasture gate timed out"
    assert data["developer_preview_only"] is True
    assert data["provider_call_was_opt_in"] is True
    assert data["persistence_allowed"] is False
    assert data["product_surface_allowed"] is False
    assert data["normal_today_surface_allowed"] is False
    assert result.succeeded is False


def test_runtime_service_does_not_mutate_database_when_payload_is_provided(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, name, starting_weight) VALUES (?, ?, ?)",
        (102, "Runtime Spike Test User", 190.0),
    )
    conn.commit()
    before = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    run_daily_coach_provider_preview_runtime_spike(
        payload=_payload(),
        model_name="qwen2.5:3b",
        provider_callable=lambda *_args: "raw free voice output",
    )

    conn = database.get_connection()
    after = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert after == before


def test_runtime_service_does_not_import_old_caged_narrative_path() -> None:
    source = inspect.getsource(runtime_service)

    forbidden_fragments = [
        "build_daily_coach_narrative_prompt",
        "run_daily_coach_narrative_candidate",
        "run_daily_coach_narrative_offline_qa",
        "DailyCoachNarrativeContext",
        "DailyCoachNarrativeOfflineQAResult",
        "DAILY_COACH_NARRATIVE_JSON_SCHEMA",
        "parse_daily_coach_narrative_candidate",
        "validate_daily_coach_narrative_candidate",
        "score_daily_coach_narrative_candidate",
        "overall_decision_for_candidate",
        "DAILY_NARRATIVE_VOICE_GOOD_EXAMPLES",
        "DAILY_NARRATIVE_VOICE_BAD_EXAMPLES",
        "DAILY_NARRATIVE_BANNED_COPY_FRAGMENTS",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_ollama_provider_call_uses_free_voice_payload_without_schema(
    monkeypatch,
) -> None:
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"response": "raw provider prose"}

    def fake_post(url: str, json: dict, timeout: float) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(runtime_service.requests, "post", fake_post)

    output = call_ollama_provider_preview_free_voice(
        "qwen2.5:3b",
        "free voice prompt",
        123.0,
        "http://localhost:11434/",
        0.9,
    )

    assert output == "raw provider prose"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 123.0
    assert captured["json"] == {
        "model": "qwen2.5:3b",
        "prompt": "free voice prompt",
        "stream": False,
        "options": {"temperature": 0.9},
    }
    assert "format" not in captured["json"]
    assert "schema" not in captured["json"]
