from __future__ import annotations

from services.ai_model_identity_service import canonical_openai_model_family


def test_known_openai_family_and_dated_snapshot_resolve_to_canonical_family() -> None:
    assert canonical_openai_model_family("gpt-5.4-mini") == "gpt-5.4-mini"
    assert canonical_openai_model_family("gpt-5.4-mini-2026-03-17") == "gpt-5.4-mini"


def test_unknown_or_arbitrary_suffix_models_remain_unresolved() -> None:
    assert canonical_openai_model_family("future-model-2026-03-17") is None
    assert canonical_openai_model_family("gpt-5.4-mini-preview") is None
    assert canonical_openai_model_family("gpt-5.4-mini-2026-3-17") is None
    assert canonical_openai_model_family("gpt-5.4-mini-2026-02-31") is None
    assert canonical_openai_model_family("gpt-5.4-mini-2026-03-17-extra") is None
