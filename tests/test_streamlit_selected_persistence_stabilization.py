from __future__ import annotations

import ast
from pathlib import Path


def _source() -> str:
    return Path("ui/streamlit_app.py").read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _source()
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function not found: {name}")


def test_active_plan_response_prefers_cached_selected_payload_after_select() -> None:
    active_source = _function_source("get_active_plan_response")

    assert "cached_response = get_cached_active_plan_response()" in active_source
    assert "cached_plan_id" in active_source
    assert "current_plan_id" in active_source
    assert "return cached_response" in active_source
    assert "current_execution_state" in active_source
