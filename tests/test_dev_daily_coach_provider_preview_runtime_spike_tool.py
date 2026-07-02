from __future__ import annotations

from dataclasses import dataclass

from tools import dev_daily_coach_provider_preview_runtime_spike as tool


@dataclass(frozen=True)
class FakePayload:
    payload_version: str = "daily_coach_provider_preview_raw_data_payload_v1"
    user_id: int = 102
    target_date: str = "2026-06-14"
    source_snapshot_version: str = "daily_coach_intelligence_snapshot_v1"

    def to_dict(self) -> dict:
        return {
            "payload_version": self.payload_version,
            "user_id": self.user_id,
            "target_date": self.target_date,
            "source_snapshot_version": self.source_snapshot_version,
            "source_data": {"recovery_intelligence": {"status": "usable"}},
        }


@dataclass(frozen=True)
class FakeResult:
    raw_model_output: str | None = "This is the model roaming in the data pasture."
    error_type: str | None = None

    def to_dict(self) -> dict:
        return {
            "result_version": "daily_coach_provider_preview_runtime_spike_result_v1",
            "user_id": 102,
            "target_date": "2026-06-14",
            "model_name": "qwen2.5:3b",
            "developer_preview_only": True,
            "provider_call_was_opt_in": True,
            "persistence_allowed": False,
            "product_surface_allowed": False,
            "normal_today_surface_allowed": False,
            "payload_version": "daily_coach_provider_preview_raw_data_payload_v1",
            "source_snapshot_version": "daily_coach_intelligence_snapshot_v1",
            "raw_model_output": self.raw_model_output,
            "error_type": self.error_type,
            "error_message": None,
        }


def test_dev_runtime_spike_tool_prints_raw_model_output_and_metadata(
    monkeypatch,
    capsys,
) -> None:
    captured: dict = {}

    def fake_build_payload(user_id: int, target_date: str | None) -> FakePayload:
        captured["payload_user_id"] = user_id
        captured["payload_target_date"] = target_date
        return FakePayload(user_id=user_id, target_date=target_date or "2026-06-14")

    def fake_run(**kwargs) -> FakeResult:
        captured["run_kwargs"] = kwargs
        return FakeResult()

    monkeypatch.setattr(
        tool,
        "build_daily_coach_provider_preview_raw_data_payload_for_user",
        fake_build_payload,
    )
    monkeypatch.setattr(
        tool, "run_daily_coach_provider_preview_runtime_spike", fake_run
    )

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--target-date",
            "2026-06-14",
            "--model",
            "qwen2.5:3b",
            "--timeout-seconds",
            "300",
            "--ollama-base-url",
            "http://localhost:11434",
            "--temperature",
            "0.9",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "DAILY COACH PROVIDER PREVIEW RUNTIME SPIKE METADATA" in output
    assert "RAW MODEL OUTPUT" in output
    assert "This is the model roaming in the data pasture." in output
    assert '"raw_model_output"' not in output.split("=== RAW MODEL OUTPUT ===")[0]
    assert captured["payload_user_id"] == 102
    assert captured["payload_target_date"] == "2026-06-14"
    assert captured["run_kwargs"]["model_name"] == "qwen2.5:3b"
    assert captured["run_kwargs"]["timeout_seconds"] == 300.0
    assert captured["run_kwargs"]["ollama_base_url"] == "http://localhost:11434"
    assert captured["run_kwargs"]["temperature"] == 0.9


def test_dev_runtime_spike_tool_can_print_payload_without_writing_files(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        tool,
        "build_daily_coach_provider_preview_raw_data_payload_for_user",
        lambda user_id, target_date: FakePayload(user_id=user_id),
    )
    monkeypatch.setattr(
        tool,
        "run_daily_coach_provider_preview_runtime_spike",
        lambda **kwargs: FakeResult(),
    )

    exit_code = tool.main(
        [
            "--user-id",
            "102",
            "--model",
            "qwen2.5:3b",
            "--print-payload",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "RAW BACKEND PAYLOAD JSON" in output
    assert "RAW MODEL OUTPUT" in output
    assert list(tmp_path.iterdir()) == []
