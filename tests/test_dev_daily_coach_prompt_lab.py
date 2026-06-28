from __future__ import annotations

from pathlib import Path

import tools.dev_daily_coach_prompt_lab as cli


def test_dev_prompt_lab_lists_scenarios(capsys) -> None:
    assert cli.main(["--list-scenarios"]) == 0
    out = capsys.readouterr().out

    assert "rich_nutrition_training_recovery" in out
    assert "2026-06-05" in out


def test_dev_prompt_lab_lists_variants(capsys) -> None:
    assert cli.main(["--list-variants"]) == 0
    out = capsys.readouterr().out

    assert "current_v5_baseline" in out
    assert "food_action_focused" in out


def test_dev_prompt_lab_run_matrix_uses_service(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    calls = {}

    class FakeSafety:
        validation_status = "not_attempted"
        rejected_phrase_flags = []

    class FakeRow:
        scenario_id = "rich_nutrition_training_recovery"
        variant_id = "current_v5_baseline"
        provider = "deterministic"
        success = True
        skipped = False
        safety_summary = FakeSafety()

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return [FakeRow()]

    monkeypatch.setattr(cli, "run_daily_coach_prompt_lab_matrix", fake_run)

    assert (
        cli.main(
            [
                "--run-matrix",
                "--scenarios",
                "rich_nutrition_training_recovery",
                "--variants",
                "current_v5_baseline",
                "--provider",
                "deterministic",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out

    assert calls["scenarios"] == ["rich_nutrition_training_recovery"]
    assert calls["variants"] == ["current_v5_baseline"]
    assert calls["provider"] == "deterministic"
    assert calls["output_dir"] == tmp_path
    assert "Prompt Lab rows: 1" in out
