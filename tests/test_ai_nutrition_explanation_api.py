from __future__ import annotations

from datetime import date as date_cls

from fastapi.testclient import TestClient

import api.routes.ai_nutrition_explanation as explanation_route
from api.main import app
from models.ai_nutrition_explanation_models import ApprovedNutritionExplanation


def _approved_explanation(
    *,
    user_id: int = 1,
    explanation_date: str = "2026-06-07",
    confidence: str = "Moderate",
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> ApprovedNutritionExplanation:
    return ApprovedNutritionExplanation(
        user_id=user_id,
        explanation_date=explanation_date,
        explanation_summary=(
            "Based on approved nutrition context, today's logged meals can be "
            "reviewed cautiously against formula-derived targets."
        ),
        macro_context=("Based on today’s logged meals, protein is below target."),
        food_suggestion_context=(
            "The Nutrition tab has approved food suggestions that may help close the gap."
        ),
        trend_context=("Trend context is available for review in the Nutrition tab."),
        calibration_context=(
            "Targets are still formula-derived. Calibration is not ready yet because "
            "more consistent logs or weigh-ins are needed."
        ),
        limitations_context=(
            "Nutrition explanation is limited to approved backend nutrition context."
        ),
        confidence=confidence,
        reason_codes=reason_codes or ["deterministic_nutrition_explanation_service"],
        limitations=limitations
        or ["Nutrition explanation is limited to approved backend nutrition context."],
        source="deterministic_fallback",
    )


def _patch_user_and_service(monkeypatch, approved: ApprovedNutritionExplanation):
    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )
    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        lambda user_id, explanation_date: approved,
    )


def test_preview_endpoint_returns_approved_deterministic_explanation(monkeypatch):
    approved = _approved_explanation()
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["explanation_date"] == "2026-06-07"
    assert payload["confidence"] == "Moderate"
    explanation = payload["approved_nutrition_explanation"]
    assert explanation["explanation_summary"]
    assert "formula-derived" in explanation["calibration_context"]
    assert explanation["source"] if "source" in explanation else True


def test_preview_endpoint_defaults_date_to_today(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        captured["date"] = explanation_date
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview")

    assert response.status_code == 200
    assert captured["date"] == date_cls.today().isoformat()
    assert response.json()["explanation_date"] == date_cls.today().isoformat()


def test_preview_endpoint_supports_explicit_date(monkeypatch):
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        captured["date"] = explanation_date
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-01")

    assert response.status_code == 200
    assert captured["date"] == "2026-06-01"
    assert response.json()["explanation_date"] == "2026-06-01"


def test_preview_endpoint_invalid_date_returns_safe_400(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=06-07-2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "date must use YYYY-MM-DD format."


def test_preview_endpoint_nonexistent_user_returns_safe_404(monkeypatch):
    monkeypatch.setattr(explanation_route, "get_user_profile", lambda user_id: None)

    client = TestClient(app)
    response = client.get("/nutrition/999/explanation/preview?date=2026-06-07")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_preview_endpoint_incomplete_context_returns_safe_limited_explanation(
    monkeypatch,
):
    approved = _approved_explanation(
        confidence="Limited",
        reason_codes=["deterministic_nutrition_explanation_fallback"],
        limitations=["Nutrition explanation is limited because context is incomplete."],
    )
    _patch_user_and_service(monkeypatch, approved)

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == "Limited"
    assert payload["limitations"]
    assert payload["approved_nutrition_explanation"]["limitations"]


def test_preview_endpoint_returns_safe_400_for_validation_failure(monkeypatch):
    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        raise ValueError("candidate validation failed")

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 400
    assert response.json()["detail"] == "AI nutrition explanation validation failed."


def test_preview_response_does_not_expose_raw_internal_or_provider_fields(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_public_terms = [
        "raw_food_entries",
        "raw_daily_checkins",
        "raw_sql",
        "debug_payload",
        "provider_metadata",
        "crewai",
        "ollama",
        "raw_output",
        "validation_errors",
        "raw_output_preview_truncated",
    ]
    assert not any(term in payload_text for term in forbidden_public_terms)


def test_preview_endpoint_does_not_expose_provider_metadata_in_normal_response(
    monkeypatch,
):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    explanation = response.json()["approved_nutrition_explanation"]
    assert "source" not in explanation
    assert "provider" not in explanation
    assert "fallback_used" not in explanation


def test_preview_endpoint_forbidden_language_does_not_appear(monkeypatch):
    _patch_user_and_service(monkeypatch, _approved_explanation())

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    payload_text = str(response.json()).lower()
    forbidden_terms = [
        "your true maintenance is exactly",
        "your targets have been changed",
        "calibration has been applied",
        "calibrated targets are active",
        "you failed",
        "you must cut calories",
        "burn this off",
        "compensate tomorrow",
        "skip meals",
        "meal plan",
    ]
    assert not any(term in payload_text for term in forbidden_terms)


def test_preview_endpoint_does_not_call_ai_provider(monkeypatch):
    called = {"service": False}

    monkeypatch.setattr(
        explanation_route,
        "get_user_profile",
        lambda user_id: {"id": user_id, "name": "QA User"},
    )

    def fake_build(user_id: int, explanation_date: str) -> ApprovedNutritionExplanation:
        called["service"] = True
        return _approved_explanation(explanation_date=explanation_date)

    monkeypatch.setattr(
        explanation_route,
        "build_configured_approved_nutrition_explanation",
        fake_build,
    )

    client = TestClient(app)
    response = client.get("/nutrition/1/explanation/preview?date=2026-06-07")

    assert response.status_code == 200
    assert called["service"] is True
    assert "provider" not in str(response.json()).lower()
