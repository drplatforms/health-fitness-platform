# QA Handoff Current

Milestone: Nutrition Catalog + Serving Foundation Planning v1

QA status: docs/project-memory planning validation only.

Branch: `feature/nutrition-catalog-serving-foundation-planning-v1`.

## QA focus

This milestone is planning/docs only. QA should validate that no runtime behavior is changed and that the planning docs are discoverable.

Primary checks:

- nutrition foundation sequence is documented;
- two-layer food catalog strategy is documented;
- serving unit / household measure strategy is documented;
- grams default/range/confidence model is documented;
- AI/provider nutrition boundary is documented;
- recommended next implementation milestone is clear;
- workout foundation is marked good enough for now;
- recovery remains acknowledged but deferred;
- no app/runtime files are changed;
- docs validation is green;
- snapshots, qa_artifacts, and patch/apply scripts are not committed.

## Expected validation

Docs-only validation:

```powershell
git diff --check
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q
scripts/dev_commit_check.ps1 -Mode docs-only
```

No browser smoke required.

No Linux runtime smoke required unless project policy chooses to pull docs milestones on Linux.
