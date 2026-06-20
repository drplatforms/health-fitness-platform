from __future__ import annotations

import ast
from pathlib import Path


def _function_source(name: str) -> str:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_today_section_places_coach_card_after_daily_next_action() -> None:
    function_source = _function_source("render_today_section")

    next_action_index = function_source.index("render_daily_next_action_panel(user_id)")
    coach_card_index = function_source.index("render_daily_coach_today_card(user_id)")
    developer_preview_index = function_source.index(
        "render_daily_coach_narrative_developer_panel(user_id)"
    )

    assert next_action_index < coach_card_index < developer_preview_index


def test_today_coach_card_uses_deterministic_today_card_route_only() -> None:
    function_source = _function_source("render_daily_coach_today_card")

    assert "/daily-coach/{user_id}/today-card" in function_source
    assert "narrative-preview" not in function_source
    assert "Run selected narrative preview" not in function_source
    assert (
        "Today’s plan is still available. Start with the next action above."
        in function_source
    )
