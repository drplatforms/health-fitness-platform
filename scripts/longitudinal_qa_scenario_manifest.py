"""Test-only factual manifest for the rich longitudinal QA personas.

This module is intentionally independent from product services. The seed script and
tests may use it to resolve date-relative phase boundaries, but it must never be
persisted or passed into Coach or longitudinal insight inputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ScenarioPhase:
    phase_id: str
    start_days_before_end: int
    end_days_before_end: int
    intended_events: tuple[str, ...]

    def contains(self, days_before_end: int) -> bool:
        return self.end_days_before_end <= days_before_end <= self.start_days_before_end


@dataclass(frozen=True)
class ProfileTransition:
    phase_id: str
    primary_goal: str
    profile_event: str


@dataclass(frozen=True)
class PersonaScenario:
    user_id: int
    scenario: str
    story_arc: str
    current_profile_state: str
    phases: tuple[ScenarioPhase, ...]
    profile_transitions: tuple[ProfileTransition, ...]
    manual_questions: tuple[str, ...]


RICH_LONGITUDINAL_QA_SCENARIOS = (
    PersonaScenario(
        user_id=104,
        scenario="improving_after_deload",
        story_arc="strength progression, plateau, deload, and rebound",
        current_profile_state="strength progression after a completed deload",
        phases=(
            ScenarioPhase(
                "foundation",
                364,
                305,
                (
                    "Established consistent three-day strength training.",
                    "Recovery and body weight were broadly stable.",
                ),
            ),
            ScenarioPhase(
                "progression",
                304,
                211,
                (
                    "Working loads increased in repeatable steps.",
                    "Recovery and nutrition logging supported the training block.",
                ),
            ),
            ScenarioPhase(
                "plateau",
                210,
                141,
                (
                    "Working loads stopped increasing while effort rose.",
                    "The strength goal remained unchanged.",
                ),
            ),
            ScenarioPhase(
                "recovery_decline",
                140,
                113,
                (
                    "Sleep and energy declined while soreness and stress increased.",
                    "Training remained frequent but completion quality softened.",
                ),
            ),
            ScenarioPhase(
                "deload",
                112,
                92,
                (
                    "Training frequency, sets, and working loads were reduced.",
                    "Recovery began improving.",
                ),
            ),
            ScenarioPhase(
                "rebound",
                91,
                28,
                (
                    "Training returned to normal frequency and loads exceeded the plateau.",
                    "Recovery and nutrition consistency improved.",
                ),
            ),
            ScenarioPhase(
                "healthy_baseline",
                27,
                21,
                ("Recovery was healthy immediately before a short fatigue event.",),
            ),
            ScenarioPhase(
                "brief_fatigue",
                20,
                7,
                ("A short high-effort stretch temporarily worsened recovery.",),
            ),
            ScenarioPhase(
                "recovery_rebound",
                6,
                0,
                ("Sleep, energy, soreness, and stress recovered in the latest week.",),
            ),
        ),
        profile_transitions=(
            ProfileTransition(
                "foundation",
                "strength_progression",
                "Established the year around repeatable strength training.",
            ),
            ProfileTransition(
                "deload",
                "strength_progression",
                "Kept the strength goal while temporarily reducing training demand.",
            ),
            ProfileTransition(
                "rebound",
                "strength_progression",
                "Returned to progression after recovery improved.",
            ),
        ),
        manual_questions=(
            "Was my recovery worse last week than the week before?",
            "Was I progressing better three months ago on Dumbbell Bench Press?",
            "When was my training going best?",
        ),
    ),
    PersonaScenario(
        user_id=103,
        scenario="nutrition_training_mismatch",
        story_arc="fat loss, improved consistency, harder training, and maintenance",
        current_profile_state="maintenance and performance after a completed fat-loss phase",
        phases=(
            ScenarioPhase(
                "baseline",
                364,
                305,
                (
                    "Body weight and training were stable with inconsistent food logging.",
                    "The saved goal was represented as a fat-loss starting context.",
                ),
            ),
            ScenarioPhase(
                "logging_consistency",
                304,
                244,
                (
                    "Nutrition logging became more complete and consistent.",
                    "Protein-rich foods appeared regularly before meaningful weight loss.",
                ),
            ),
            ScenarioPhase(
                "fat_loss",
                243,
                153,
                (
                    "Body weight declined at a gradual, plausible rate.",
                    "Training remained productive with mostly usable recovery.",
                ),
            ),
            ScenarioPhase(
                "harder_training",
                152,
                92,
                (
                    "Training effort increased and some final sets missed target reps.",
                    "Weight loss continued more slowly.",
                ),
            ),
            ScenarioPhase(
                "logging_disruption",
                91,
                61,
                (
                    "Schedule pressure caused missing and partial nutrition logs.",
                    "Recorded intake must not be treated as complete intake.",
                ),
            ),
            ScenarioPhase(
                "maintenance_recovery",
                60,
                0,
                (
                    "The goal shifted to maintenance and performance.",
                    "Body weight stabilized while recovery and nutrition consistency improved.",
                ),
            ),
        ),
        profile_transitions=(
            ProfileTransition(
                "baseline",
                "fat_loss",
                "Started with a gradual fat-loss goal and a 174 lb goal weight.",
            ),
            ProfileTransition(
                "maintenance_recovery",
                "maintenance_and_performance",
                "Shifted to maintenance and performance after the fat-loss phase.",
            ),
        ),
        manual_questions=(
            "What changed when my weight started dropping?",
            "What changed over the last month?",
            "What are the biggest changes across the last six months or year?",
        ),
    ),
    PersonaScenario(
        user_id=101,
        scenario="recovery_limited",
        story_arc="variable sleep and schedule, missed training, and productive return",
        current_profile_state="strength and recomposition with recovery-aware scheduling",
        phases=(
            ScenarioPhase(
                "stable_start",
                364,
                305,
                ("Training attendance and sleep were initially stable.",),
            ),
            ScenarioPhase(
                "schedule_disruption",
                304,
                244,
                (
                    "Sleep and nutrition logging became variable as schedule stress increased.",
                    "Some planned training days were missed.",
                ),
            ),
            ScenarioPhase(
                "attempted_return",
                243,
                184,
                ("Training attendance improved before recovery fully stabilized.",),
            ),
            ScenarioPhase(
                "recurring_stress",
                183,
                124,
                ("A second sleep and stress decline repeated the earlier pattern.",),
            ),
            ScenarioPhase(
                "missed_training",
                123,
                92,
                (
                    "Training frequency dropped and nutrition records were often partial.",
                ),
            ),
            ScenarioPhase(
                "recovery_swings",
                91,
                31,
                ("Recovery alternated between usable and limited weeks.",),
            ),
            ScenarioPhase(
                "productive_return",
                30,
                0,
                (
                    "Training attendance returned without aggressive load jumps.",
                    "Sleep improved but soreness remained a relevant constraint.",
                ),
            ),
        ),
        profile_transitions=(
            ProfileTransition(
                "stable_start",
                "strength_and_recomposition",
                "Started with a strength and recomposition goal.",
            ),
            ProfileTransition(
                "schedule_disruption",
                "strength_and_recomposition",
                "Kept the goal but adopted recovery-aware scheduling.",
            ),
            ProfileTransition(
                "productive_return",
                "strength_and_recomposition",
                "Returned productively without changing the saved end-state goal.",
            ),
        ),
        manual_questions=(
            "Was my recovery worse last week than the week before?",
            "What patterns keep repeating?",
            "When was my training going best?",
        ),
    ),
)


def scenario_for_user(user_id: int) -> PersonaScenario | None:
    return next(
        (
            scenario
            for scenario in RICH_LONGITUDINAL_QA_SCENARIOS
            if scenario.user_id == user_id
        ),
        None,
    )


def phase_id_for(user_id: int, days_before_end: int) -> str | None:
    scenario = scenario_for_user(user_id)
    if scenario is None:
        return None
    phase = next(
        (phase for phase in scenario.phases if phase.contains(days_before_end)),
        None,
    )
    return phase.phase_id if phase is not None else None


def build_longitudinal_qa_scenario_manifest(end_date: date) -> dict[str, object]:
    """Resolve the test-only manifest to concrete dates for QA assertions."""

    personas: list[dict[str, object]] = []
    for scenario in RICH_LONGITUDINAL_QA_SCENARIOS:
        payload = asdict(scenario)
        payload["phases"] = [
            {
                **asdict(phase),
                "start_date": (
                    end_date - timedelta(days=phase.start_days_before_end)
                ).isoformat(),
                "end_date": (
                    end_date - timedelta(days=phase.end_days_before_end)
                ).isoformat(),
            }
            for phase in scenario.phases
        ]
        personas.append(payload)
    return {
        "manifest_version": "rich_longitudinal_qa_dataset_v1",
        "end_date": end_date.isoformat(),
        "personas": personas,
        "controls": [
            {
                "user_id": 102,
                "scenario": "aligned_managed",
                "purpose": "stable, densely logged baseline with the existing training comparison arc",
            },
            {
                "user_id": 105,
                "scenario": "data_quality_limited",
                "purpose": "sparse and incomplete data suppression control",
            },
        ],
    }
