from __future__ import annotations

import json
from dataclasses import dataclass

from tools import dev_daily_coach_provider_preview_payload as tool


@dataclass(frozen=True)
class FakePayload:
    def to_dict(self) -> dict:
        return {
            "payload_version": "daily_coach_provider_preview_raw_data_payload_v1",
            "user_id": 102,
            "target_date": "2026-06-14",
            "developer_preview_only": True,
            "provider_call_allowed": False,
            "persistence_allowed": False,
            "product_surface_allowed": False,
            "source_data": {
                "recovery_intelligence": {"confidence": "Moderate"},
                "foundation_layer_status": {"recovery_intelligence": "implemented_v1"},
            },
            "provider_voice_space": {
                "do_not_force_sentence_bank": True,
                "do_not_reduce_input_to_backend_prose_summary": True,
            },
        }


def test_developer_tool_prints_json_to_terminal(monkeypatch, capsys) -> None:
    calls = []

    def _fake_builder(*, user_id: int, target_date: str | None):
        calls.append({"user_id": user_id, "target_date": target_date})
        return FakePayload()

    monkeypatch.setattr(
        tool,
        "build_daily_coach_provider_preview_raw_data_payload_for_user",
        _fake_builder,
    )

    exit_code = tool.main(["--user-id", "102", "--target-date", "2026-06-14"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert calls == [{"user_id": 102, "target_date": "2026-06-14"}]
    assert payload["developer_preview_only"] is True
    assert payload["provider_call_allowed"] is False
    assert payload["persistence_allowed"] is False
    assert payload["product_surface_allowed"] is False
    assert payload["source_data"]["recovery_intelligence"]["confidence"] == "Moderate"


def test_developer_tool_does_not_import_provider_runtime_modules() -> None:
    source = tool.Path(tool.__file__).read_text(encoding="utf-8").lower()

    assert "crewai" not in source
    assert "openai" not in source
    assert "ollama" not in source
    assert "provider_service" not in source
