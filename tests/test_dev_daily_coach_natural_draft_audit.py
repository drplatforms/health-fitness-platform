from __future__ import annotations

from pathlib import Path

import tools.dev_daily_coach_natural_draft_audit as cli


def test_dev_natural_draft_audit_lists_scenarios(capsys) -> None:
    assert cli.main(["--list-scenarios"]) == 0
    out = capsys.readouterr().out

    assert "rich_nutrition_training_recovery" in out
    assert "2026-06-05" in out


def test_dev_natural_draft_audit_run_scenario_uses_service(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    calls = {}

    class FakeAudit:
        passed = True

    class FakeRepair:
        attempted = False

    class FakeRow:
        scenario_id = "rich_nutrition_training_recovery"
        provider = "deterministic"
        final_source = "draft_approved"
        audit_result = FakeAudit()
        repair_result = FakeRepair()

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return FakeRow()

    monkeypatch.setattr(cli, "run_daily_coach_natural_draft_audit_scenario", fake_run)

    assert (
        cli.main(
            [
                "--run-scenario",
                "rich_nutrition_training_recovery",
                "--provider",
                "deterministic",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out

    assert calls["scenario_id"] == "rich_nutrition_training_recovery"
    assert calls["provider"] == "deterministic"
    assert calls["output_dir"] == tmp_path
    assert "Natural Draft Audit rows: 1" in out


def test_dev_natural_draft_audit_run_matrix_uses_service(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    calls = {}

    class FakeAudit:
        passed = True

    class FakeRepair:
        attempted = False

    class FakeRow:
        scenario_id = "rich_nutrition_training_recovery"
        provider = "deterministic"
        final_source = "draft_approved"
        audit_result = FakeAudit()
        repair_result = FakeRepair()

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return [FakeRow()]

    monkeypatch.setattr(cli, "run_daily_coach_natural_draft_audit_matrix", fake_run)

    assert (
        cli.main(
            [
                "--run-matrix",
                "--scenarios",
                "rich_nutrition_training_recovery",
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
    assert calls["provider"] == "deterministic"
    assert calls["output_dir"] == tmp_path
    assert "Natural Draft Audit rows: 1" in out
