from __future__ import annotations

import ast
from pathlib import Path

STREAMLIT_SOURCE = Path("ui/streamlit_app.py")


def _source() -> str:
    return STREAMLIT_SOURCE.read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _source()
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_today_polish_removes_garnet_gold_palette() -> None:
    source = _source()

    assert "garnet/gold" not in source.lower()
    assert "#CEB888" not in source
    assert "#782F40" not in source
    assert "#F2C75C" not in source
    assert "Today UX Polish v1 — calm neutral product palette" in source


def test_next_action_uses_calm_card_instead_of_heavy_alert_banner() -> None:
    function_source = _function_source("render_daily_next_action_panel")

    assert "Your next move" in function_source
    assert "portfolio-card-action" in function_source
    assert "Start here" in function_source
    assert "Why this matters" in function_source
    assert 'st.warning(f"**{action.get' not in function_source
    assert 'st.success(f"**{action.get' not in function_source
    assert 'st.info(f"**{action.get' not in function_source


def test_today_coach_card_uses_integrated_focus_card_copy() -> None:
    function_source = _function_source("render_daily_coach_today_card")

    assert "Today’s Focus" in function_source
    assert "portfolio-card-coach" in function_source
    assert "Why this matters" in function_source
    assert "Today???s" not in function_source
    assert "narrative-preview" not in function_source


def test_workout_substitution_copy_uses_clear_swap_flow_without_algorithm_change() -> (
    None
):
    display_source = _function_source("display_substitution_candidates")
    apply_source = _function_source("display_apply_substitution_control")

    assert "Need a swap?" in display_source
    assert "Choose an exercise to replace" in display_source
    assert "Replace:" in display_source
    assert "Original exercise" in display_source
    assert "Suggested swaps" in apply_source
    assert "Swap in" in apply_source
    assert "Choose a replacement exercise" in apply_source
    assert "get_substitution_candidates(" not in display_source
    assert "apply_substitution(" not in apply_source


def test_normal_ui_polish_does_not_introduce_provider_or_debug_terms() -> None:
    normal_functions = (
        _function_source("render_daily_next_action_panel")
        + _function_source("render_daily_coach_today_card")
        + _function_source("display_substitution_candidates")
        + _function_source("display_apply_substitution_control")
    )

    forbidden_terms = [
        "qwen",
        "ollama",
        "direct_ollama",
        "fallback_reason",
        "raw_response",
        "prompt",
        "provider_attempted",
        "selected_model",
    ]

    for term in forbidden_terms:
        assert term not in normal_functions
