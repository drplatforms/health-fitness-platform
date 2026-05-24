from types import SimpleNamespace

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services import coordinator_service


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def _disable_report_persistence(monkeypatch):
    monkeypatch.setattr(
        coordinator_service,
        "save_health_report",
        lambda user_id, report_text, model_summary: None,
    )


def test_health_report_defaults_to_deterministic_provider(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _disable_report_persistence(monkeypatch)
    monkeypatch.delenv("HEALTH_REPORT_PROVIDER", raising=False)
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")

    report = coordinator_service.generate_health_report(105)
    metadata = coordinator_service.get_latest_report_runtime_metadata(105)

    assert "Grounded Recommendation" in report
    assert metadata["report_provider"] == "deterministic"
    assert metadata["crewai_report_attempted"] is False
    assert metadata["report_fallback_used"] is False
    assert metadata["report_fallback_reason"] == "deterministic_selected"
    assert metadata["elapsed_seconds"] >= 0


def test_health_report_invalid_provider_falls_back_to_deterministic(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    _disable_report_persistence(monkeypatch)
    monkeypatch.setenv("HEALTH_REPORT_PROVIDER", "not-a-provider")
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")

    report = coordinator_service.generate_health_report(105)
    metadata = coordinator_service.get_latest_report_runtime_metadata(105)

    assert "Data quality limits confidence" in report
    assert metadata["report_provider"] == "deterministic"
    assert metadata["crewai_report_attempted"] is False
    assert metadata["report_fallback_used"] is True
    assert metadata["report_fallback_reason"] == "invalid_provider"


def test_health_report_crewai_timeout_falls_back_safely(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _disable_report_persistence(monkeypatch)
    monkeypatch.setenv("HEALTH_REPORT_PROVIDER", "crewai")
    monkeypatch.setenv("RECOMMENDATION_CANDIDATE_PROVIDER", "deterministic")

    class FakeLLM:
        def __init__(self, *args, **kwargs):
            pass

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            pass

    class FakeTask:
        def __init__(self, *args, **kwargs):
            pass

    class FakeCrew:
        def __init__(self, *args, **kwargs):
            pass

        def kickoff(self):
            return SimpleNamespace(raw="should not be used")

    monkeypatch.setitem(
        __import__("sys").modules,
        "crewai",
        SimpleNamespace(LLM=FakeLLM, Agent=FakeAgent, Crew=FakeCrew, Task=FakeTask),
    )

    def raise_timeout(callback, timeout_seconds):
        raise coordinator_service.HealthReportTimeoutError("timed out")

    monkeypatch.setattr(
        coordinator_service,
        "_run_report_with_timeout",
        raise_timeout,
    )

    report = coordinator_service.generate_health_report(105)
    metadata = coordinator_service.get_latest_report_runtime_metadata(105)

    assert "Data quality limits confidence" in report
    assert metadata["report_provider"] == "crewai"
    assert metadata["crewai_report_attempted"] is True
    assert metadata["report_fallback_used"] is True
    assert metadata["report_fallback_reason"] == "crewai_timeout"
    assert "overtraining" not in report.lower()
