from __future__ import annotations

import tools.dev_daily_coach_wide_context_ceiling_trial as cli


def test_dev_wide_context_trial_lists_variants(capsys) -> None:
    exit_code = cli.main(["--list-variants"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "wide_context_minimal_prompt" in output
    assert "current_narrow_path" in output


def test_dev_wide_context_trial_run_scenario_uses_service(
    monkeypatch, tmp_path, capsys
) -> None:
    class FakeResult:
        scenario_id = "rich_nutrition_training_recovery"
        provider = "deterministic"
        model = "gpt-5.5"
        variants = []

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        assert kwargs["scenario_id"] == "rich_nutrition_training_recovery"
        assert kwargs["provider"] == "deterministic"
        assert kwargs["output_dir"] == tmp_path
        return FakeResult()

    monkeypatch.setattr(
        cli, "run_daily_coach_wide_context_ceiling_trial_scenario", fake_run
    )

    exit_code = cli.main(
        [
            "--run-scenario",
            "rich_nutrition_training_recovery",
            "--output-dir",
            str(tmp_path),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wide Context Ceiling Trial runs: 1" in output
    assert "Known baseline drift documented" in output


def test_dev_wide_context_trial_run_matrix_uses_service(
    monkeypatch, tmp_path, capsys
) -> None:
    class FakeResult:
        scenario_id = "stable_comparison"
        provider = "openai"
        model = "gpt-5.5"
        variants = []

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        assert kwargs["scenarios"] == ["stable_comparison"]
        assert kwargs["provider"] == "openai"
        assert kwargs["model"] == "gpt-5.5"
        assert kwargs["allow_live_provider"] is True
        return [FakeResult()]

    monkeypatch.setattr(
        cli, "run_daily_coach_wide_context_ceiling_trial_matrix", fake_run
    )

    exit_code = cli.main(
        [
            "--run-matrix",
            "--scenarios",
            "stable_comparison",
            "--provider",
            "openai",
            "--model",
            "gpt-5.5",
            "--allow-live-provider",
            "--output-dir",
            str(tmp_path),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "stable_comparison" in output


def test_dev_wide_context_trial_accepts_pasteback_and_print_flags(
    monkeypatch, tmp_path, capsys
) -> None:
    class FakeVariant:
        skipped = False

    class FakeResult:
        scenario_id = "stable_comparison"
        provider = "deterministic"
        model = "gpt-5.5"
        variants = [FakeVariant()]

        def to_dict(self):
            return {"scenario_id": self.scenario_id}

    def fake_run(**kwargs):
        output_dir = kwargs["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "first_pass_drafts_compact.md").write_text(
            "compact first pass", encoding="utf-8"
        )
        (output_dir / "best_variant_summary.md").write_text(
            "best variant", encoding="utf-8"
        )
        (output_dir / "product_language_findings.md").write_text(
            "product issues", encoding="utf-8"
        )
        (output_dir / "pasteback_report.md").write_text("pasteback", encoding="utf-8")
        return FakeResult()

    monkeypatch.setattr(
        cli, "run_daily_coach_wide_context_ceiling_trial_scenario", fake_run
    )

    exit_code = cli.main(
        [
            "--run-scenario",
            "stable_comparison",
            "--output-dir",
            str(tmp_path),
            "--write-pasteback-report",
            "--print-first-pass",
            "--print-best-variant",
            "--print-product-issues",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Pasteback report:" in output
    assert "compact first pass" in output
    assert "best variant" in output
    assert "product issues" in output
