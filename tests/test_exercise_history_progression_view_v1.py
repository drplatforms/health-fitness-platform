from __future__ import annotations

from pathlib import Path

COMPONENT_SOURCE = Path(
    "frontend/src/components/WorkoutHistoryAnalytics.tsx"
).read_text(encoding="utf-8")


def test_selected_exercise_displays_existing_progression_recommendation() -> None:
    assert "Current progression recommendation" in COMPONENT_SOURCE
    assert "Current recommendation" in COMPONENT_SOURCE
    assert "recommendation.headline" in COMPONENT_SOURCE
    assert "recommendation.target_guidance" in COMPONENT_SOURCE


def test_recent_sessions_display_completed_set_reps_load_and_optional_rir() -> None:
    assert "session.completed_sets.map" in COMPONENT_SOURCE
    assert "Set {set.set_number}" in COMPONENT_SOURCE
    assert "`${set.actual_reps} reps`" in COMPONENT_SOURCE
    assert "`${formatHistoryNumber(set.actual_weight)} lb`" in COMPONENT_SOURCE
    assert "`RIR ${set.actual_rir}`" in COMPONENT_SOURCE
    assert "Completed sets for" in COMPONENT_SOURCE
