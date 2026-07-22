from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Any

from models.coach_models import (
    CoachConfidence,
    CoachConversationTurn,
    CoachEvidenceItem,
    CoachEvidencePack,
)
from models.exercise_catalog_models import ExerciseCatalogEntry
from models.longitudinal_insight_models import LongitudinalInsight
from services.equipment_profile_service import get_effective_equipment_profile
from services.exercise_catalog_service import get_exercise_catalog
from services.longitudinal_insight_service import build_longitudinal_insight_feed
from services.nutrition_trend_service import build_nutrition_trend_window
from services.recovery_intelligence_v2_service import build_recovery_intelligence_v2
from services.user_service import get_user_profile
from services.workout_exercise_history_analytics_service import (
    ExerciseHistoryAnalyticsSummary,
    WorkoutExerciseHistoryAnalytics,
    build_workout_exercise_history_analytics,
)
from services.workout_exercise_profile_service import (
    get_workout_exercise_preference_map,
)
from services.workout_progression_decision_service import comparable_working_weight
from services.workout_progression_history_service import (
    ExerciseProgressionSession,
    completed_exercise_actual_rows,
    load_completed_user_progression_sessions,
)

COACH_EVIDENCE_PACK_VERSION = "grounded_coach_evidence_v1"
MAX_CONVERSATION_TURNS = 6
MAX_CONVERSATION_TURN_CHARS = 600
MAX_CONVERSATION_TOTAL_CHARS = 2400
MAX_EVIDENCE_PROMPT_CHARS = 12_000
MAX_BASELINE_LONGITUDINAL_ITEMS = 4
MAX_DEEP_LONGITUDINAL_ITEMS = 4
BASELINE_TRAINING_LOOKBACK_DAYS = 28
HISTORICAL_EXERCISE_LOOKBACK_DAYS = 365

_RECOVERY_TERMS = {
    "recovery",
    "recovering",
    "sleep",
    "energy",
    "soreness",
    "stress",
    "pain",
    "fatigue",
    "readiness",
    "motivation",
}
_TRAINING_TERMS = {
    "training",
    "workout",
    "workouts",
    "exercise",
    "exercises",
    "progress",
    "progressing",
    "strength",
    "load",
    "rir",
    "reps",
    "sets",
    "harder",
    "easier",
}
_NUTRITION_TERMS = {
    "nutrition",
    "food",
    "eating",
    "calorie",
    "calories",
    "protein",
    "carbs",
    "fat",
    "logging",
    "logged",
}
_BODY_WEIGHT_TERMS = {"bodyweight", "weigh", "weighin", "weighins", "scale"}
_PROFILE_TERMS = {"goal", "goals", "target", "progress"}
_EQUIPMENT_TERMS = {
    "equipment",
    "gym",
    "home gym",
    "substitute",
    "alternative",
    "favorite",
    "favourite",
    "dislike",
    "prefer",
}
_AVAILABLE_EQUIPMENT_CONTEXT_TERMS = {
    "barbell",
    "barbells",
    "bench",
    "bike",
    "cable",
    "cables",
    "dumbbell",
    "dumbbells",
    "machine",
    "machines",
    "rack",
    "resistance band",
    "resistance bands",
    "treadmill",
}
_BROAD_PHRASES = (
    "am i making progress",
    "how am i doing",
    "what changed",
    "what patterns",
    "patterns have you noticed",
    "overall progress",
    "last month",
    "past month",
)
_ALWAYS_BROAD_PHRASES = (
    "am i making progress",
    "how am i doing",
    "overall progress",
)
_HISTORICAL_COMPARISON_PHRASES = (
    "over time",
    "was i progressing better",
    "were i progressing better",
    "making better progress",
    "how has it changed",
    "how has this changed",
    "how has that changed",
    "used to",
)
_ACTION_FOLLOW_UP_PREFIXES = (
    "what would you suggest",
    "what do you suggest",
    "what should i",
    "can i",
    "could i",
    "should i",
    "would it",
)
_EXERCISE_NAME_ALIASES = {
    "rdl": "Romanian Deadlift",
    "rdls": "Romanian Deadlift",
}
_CONFIDENCE_ORDER: dict[str, int] = {
    "Limited": 0,
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}
_SUBJECTIVE_RECOVERY_SCALES: dict[str, tuple[int, int]] = {
    "sleep_quality": (1, 5),
    "energy_level": (1, 10),
    "soreness_level": (1, 10),
    "stress_level": (1, 5),
    "training_motivation": (1, 5),
}


@dataclass(frozen=True)
class _ExerciseProgressionExposure:
    performed_at: date
    comparable_working_weight: float
    average_actual_rir: float


@dataclass(frozen=True)
class _ExerciseComparisonPhase:
    window_start: str
    window_end: str
    prior_weight: float
    recent_weight: float
    prior_rir: float
    recent_rir: float


@dataclass(frozen=True)
class _ExerciseHistoricalComparison:
    earlier_progression: _ExerciseComparisonPhase
    current_phase: _ExerciseComparisonPhase


def bound_coach_conversation_context(
    turns: Sequence[CoachConversationTurn | Mapping[str, Any]],
) -> tuple[CoachConversationTurn, ...]:
    normalized: list[CoachConversationTurn] = []
    remaining_chars = MAX_CONVERSATION_TOTAL_CHARS
    for raw_turn in reversed(list(turns)[-MAX_CONVERSATION_TURNS:]):
        role = (
            raw_turn.role
            if isinstance(raw_turn, CoachConversationTurn)
            else raw_turn.get("role")
        )
        content = (
            raw_turn.content
            if isinstance(raw_turn, CoachConversationTurn)
            else raw_turn.get("content")
        )
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        compact = " ".join(content.split())[:MAX_CONVERSATION_TURN_CHARS]
        if not compact or remaining_chars <= 0:
            continue
        compact = compact[:remaining_chars]
        normalized.append(CoachConversationTurn(role=role, content=compact))
        remaining_chars -= len(compact)
    normalized.reverse()
    return tuple(normalized)


def build_coach_evidence_pack(
    *,
    user_id: int,
    question: str,
    conversation_context: Sequence[CoachConversationTurn | Mapping[str, Any]] = (),
    as_of_date: str | date | None = None,
) -> CoachEvidencePack:
    profile_row = get_user_profile(user_id)
    if profile_row is None:
        raise ValueError(f"User with id {user_id} was not found.")

    target = _resolve_date(as_of_date)
    bounded_turns = bound_coach_conversation_context(conversation_context)
    catalog = get_exercise_catalog()
    prior_user_questions = [
        turn.content for turn in reversed(bounded_turns) if turn.role == "user"
    ]
    prior_user_question = prior_user_questions[0] if prior_user_questions else None
    prior_subject_question = next(
        (
            prior_question
            for prior_question in prior_user_questions
            if resolve_referenced_exercise(prior_question, catalog) is not None
        ),
        None,
    )
    matched_exercise = resolve_referenced_exercise(question, catalog)
    follow_up = prior_user_question is not None and _looks_like_follow_up(question)
    if (
        matched_exercise is None
        and follow_up
        and not _has_explicit_non_training_subject(question)
    ):
        matched_exercise = resolve_referenced_exercise(
            prior_subject_question or prior_user_question,
            catalog,
        )
    classification_text = question
    if follow_up and not _has_explicit_question_subject(question, catalog):
        classification_text = (
            f"{prior_subject_question or prior_user_question} {question}"
        )
    topics = classify_coach_question(classification_text)
    if matched_exercise is not None and "training" not in topics:
        topics = (*topics, "training")
    historical_comparison_requested = (
        matched_exercise is not None and _has_historical_comparison_intent(question)
    )
    if historical_comparison_requested:
        topics = (*topics, "historical_comparison")
    if (
        matched_exercise is not None
        and {"harder", "easier"}.intersection(_normalize(question).split())
        and "recovery" not in topics
    ):
        topics = (*topics, "recovery")

    broad = "broad" in topics
    source_services = [
        "user_service",
        "longitudinal_insight_service",
        "recovery_intelligence_v2_service",
        "nutrition_trend_service",
        "workout_exercise_history_analytics_service",
    ]
    insight_feed = build_longitudinal_insight_feed(
        user_id=user_id,
        as_of_date=target,
        max_insights=10,
    )
    insights: Sequence[LongitudinalInsight] = insight_feed.insights
    recovery = build_recovery_intelligence_v2(
        user_id=user_id,
        target_date=target,
    )
    nutrition = build_nutrition_trend_window(
        user_id=user_id,
        end_date=target.isoformat(),
        window_days=28,
    )
    baseline_training = build_workout_exercise_history_analytics(
        user_id=user_id,
        lookback_days=BASELINE_TRAINING_LOOKBACK_DAYS,
        exercise_limit=1,
        session_limit=1,
        end_date=target.isoformat(),
    )

    training = baseline_training
    if broad or "training" in topics or matched_exercise is not None:
        training = build_workout_exercise_history_analytics(
            user_id=user_id,
            lookback_days=180,
            exercise_limit=48,
            session_limit=8,
            end_date=target.isoformat(),
        )

    historical_comparison = None
    if historical_comparison_requested and matched_exercise is not None:
        historical_comparison = _build_exercise_historical_comparison(
            user_id=user_id,
            matched_exercise=matched_exercise,
            end_date=target,
        )
        source_services.append("workout_progression_history_service")

    equipment = None
    preferences: Mapping[int, str] = {}
    if "equipment" in topics or matched_exercise is not None:
        equipment = get_effective_equipment_profile(user_id)
        preferences = get_workout_exercise_preference_map(user_id)
        source_services.extend(
            ["equipment_profile_service", "workout_exercise_profile_service"]
        )

    return build_coach_evidence_pack_from_sources(
        user_id=user_id,
        question=question,
        as_of_date=target.isoformat(),
        topics=topics,
        user_profile=dict(profile_row),
        insights=insights,
        recovery=recovery,
        nutrition=nutrition,
        baseline_training=baseline_training,
        training=training,
        matched_exercise=matched_exercise,
        historical_comparison=historical_comparison,
        equipment=equipment,
        exercise_preferences=preferences,
        source_services=source_services,
    )


def build_coach_evidence_pack_from_sources(
    *,
    user_id: int,
    question: str,
    as_of_date: str,
    topics: Sequence[str],
    user_profile: Mapping[str, Any],
    insights: Sequence[LongitudinalInsight],
    recovery: Any | None = None,
    nutrition: Any | None = None,
    baseline_training: WorkoutExerciseHistoryAnalytics | None = None,
    training: WorkoutExerciseHistoryAnalytics | None = None,
    matched_exercise: ExerciseCatalogEntry | None = None,
    historical_comparison: _ExerciseHistoricalComparison | None = None,
    equipment: Any | None = None,
    exercise_preferences: Mapping[int, str] | None = None,
    source_services: Sequence[str] = (),
) -> CoachEvidencePack:
    del question  # Question classification is represented by the explicit topics.
    topic_set = set(topics)
    broad = "broad" in topic_set
    baseline_items: list[CoachEvidenceItem] = []
    depth_items: list[CoachEvidenceItem] = []
    limitations: list[str] = []

    goal = _clean_value(user_profile.get("primary_goal"))
    if goal:
        baseline_items.append(
            _item(
                "profile:primary_goal",
                "profile",
                "user_goal",
                "Primary goal",
                f"The saved primary goal is {_humanize(goal)}.",
                "High",
                "users.primary_goal",
                structured_data={"primary_goal": goal},
            )
        )

    baseline_training_source = baseline_training or training
    training_overview_item = _training_overview_item(
        baseline_training_source,
        window_days=BASELINE_TRAINING_LOOKBACK_DAYS,
        window_end=as_of_date,
    )
    if training_overview_item is not None:
        baseline_items.append(training_overview_item)

    recovery_items = _recovery_items(recovery) if recovery is not None else []
    if recovery_items:
        current_recovery = next(
            (
                item
                for item in recovery_items
                if item.evidence_type == "current_recovery_checkin"
            ),
            recovery_items[0],
        )
        baseline_items.append(current_recovery)
        if broad or "recovery" in topic_set:
            depth_items.extend(
                item for item in recovery_items if item is not current_recovery
            )
    if recovery is not None and (broad or "recovery" in topic_set):
        limitations.extend(getattr(recovery, "limitations", [])[:2])

    if nutrition is not None:
        baseline_items.extend(_nutrition_items(nutrition, include_weight=True))
        if broad or {"nutrition", "body_weight"}.intersection(topic_set):
            limitations.extend(getattr(nutrition, "limitations", [])[:2])

    baseline_longitudinal = _baseline_longitudinal_items(insights)
    baseline_items.extend(baseline_longitudinal)

    if matched_exercise is not None:
        exercise_id = matched_exercise.id
        reference_base = f"exercise:{exercise_id or _token(matched_exercise.name)}"
        equipment_text = ", ".join(
            _humanize(value) for value in matched_exercise.equipment_required
        )
        fact = (
            f"{matched_exercise.name} is the matched catalog exercise"
            + (f" and uses {equipment_text}" if equipment_text else "")
            + "."
        )
        depth_items.append(
            _item(
                f"{reference_base}:catalog",
                "training",
                "exercise_identity",
                matched_exercise.name,
                fact,
                "High",
                "exercise_catalog_service",
                structured_data={
                    "catalog_exercise_id": matched_exercise.id,
                    "name": matched_exercise.name,
                    "exercise_type": matched_exercise.exercise_type,
                    "movement_pattern": matched_exercise.movement_pattern,
                    "primary_muscle_groups": list(
                        matched_exercise.primary_muscle_groups
                    ),
                    "equipment_required": list(matched_exercise.equipment_required),
                },
            )
        )
        exercise_history = _matching_exercise_history(training, matched_exercise)
        if exercise_history is None:
            limitations.append(
                f"No completed {matched_exercise.name} history was available in the bounded lookback."
            )
        else:
            depth_items.extend(
                _exercise_history_items(reference_base, exercise_history)
            )
            if exercise_history.limitation:
                limitations.append(exercise_history.limitation)

        if "historical_comparison" in topic_set:
            if historical_comparison is None:
                limitations.append(
                    f"The bounded longer history did not contain both an earlier comparable progression phase and a current comparison for {matched_exercise.name}."
                )
            else:
                depth_items.extend(
                    _historical_comparison_items(
                        reference_base,
                        matched_exercise.name,
                        historical_comparison,
                    )
                )

        preference = (
            (exercise_preferences or {}).get(exercise_id)
            if exercise_id is not None
            else None
        )
        if preference in {"favorite", "disliked"}:
            depth_items.append(
                _item(
                    f"{reference_base}:preference",
                    "preferences",
                    "exercise_preference",
                    "Saved exercise preference",
                    f"{matched_exercise.name} is saved as {preference}.",
                    "High",
                    "workout_exercise_profile_service",
                    structured_data={
                        "exercise_name": matched_exercise.name,
                        "preference": preference,
                    },
                )
            )

    baseline_references = {item.reference_id for item in _dedupe_items(baseline_items)}
    depth_items.extend(
        _depth_longitudinal_items(
            insights,
            relevant_domains=_relevant_insight_domains(topic_set),
            broad=broad,
            matched_exercise_name=(
                matched_exercise.name if matched_exercise is not None else None
            ),
            excluded_references=baseline_references,
        )
    )

    if training_overview_item is None and (
        broad or "training" in topic_set or matched_exercise is not None
    ):
        limitations.append(
            "No completed workout history was available in the bounded lookback."
        )

    if equipment is not None and "equipment" in topic_set:
        confidence = getattr(equipment, "confidence", "Low")
        if confidence != "Low":
            available = list(getattr(equipment, "available_equipment", []))
            if available:
                depth_items.append(
                    _item(
                        "equipment:available",
                        "equipment",
                        "equipment_profile",
                        "Available equipment",
                        "The saved equipment profile includes "
                        + ", ".join(_humanize(value) for value in available[:12])
                        + ".",
                        _confidence(confidence),
                        "equipment_profile_service",
                        structured_data={"available_equipment": available[:12]},
                    )
                )
        else:
            limitations.append("No explicit equipment profile was available.")

    limitations = _dedupe_text(limitations)[:6]
    matched_context = _matched_exercise_context(matched_exercise)
    items = _fit_evidence_items_to_prompt_budget(
        _dedupe_items([*baseline_items, *depth_items]),
        user_id=user_id,
        as_of_date=as_of_date,
        topics=topics,
        matched_exercise_name=(matched_exercise.name if matched_exercise else None),
        matched_exercise_context=matched_context,
        limitations=limitations,
    )
    if not items:
        limitations.append(
            "The available history did not contain enough supported evidence for this question."
        )
        limitations = _dedupe_text(limitations)[:6]
    confidence = _pack_confidence(items)
    if "historical_comparison" in topic_set and not {
        "exercise_historical_progression_phase",
        "exercise_current_comparison_phase",
    }.issubset({item.evidence_type for item in items}):
        confidence = "Limited"
    return CoachEvidencePack(
        pack_version=COACH_EVIDENCE_PACK_VERSION,
        user_id=user_id,
        as_of_date=as_of_date,
        question_topics=tuple(topics),
        matched_exercise_name=(matched_exercise.name if matched_exercise else None),
        evidence=tuple(items),
        limitations=tuple(limitations),
        source_services=tuple(dict.fromkeys(source_services)),
        confidence=confidence,
        matched_exercise_context=matched_context,
    )


def _training_overview_item(
    training: WorkoutExerciseHistoryAnalytics | None,
    *,
    window_days: int,
    window_end: str,
) -> CoachEvidenceItem | None:
    if training is None or not training.overview.has_history:
        return None
    overview = training.overview
    return _item(
        "training:history-overview",
        "training",
        "training_history_overview",
        "Recent training history",
        (
            f"The recent {window_days}-day training window contains "
            f"{overview.completed_workout_count} completed workouts and "
            f"{overview.completed_set_count} completed sets across "
            f"{overview.distinct_effective_exercise_count} exercises."
        ),
        "High",
        "workout_exercise_history_analytics_service",
        overview.most_recent_completed_workout_date,
        structured_data={
            "window_days": window_days,
            "window_end": window_end,
            "completed_workout_count": overview.completed_workout_count,
            "completed_set_count": overview.completed_set_count,
            "distinct_effective_exercise_count": (
                overview.distinct_effective_exercise_count
            ),
            "most_recent_completed_workout_date": (
                overview.most_recent_completed_workout_date
            ),
        },
    )


def _matched_exercise_context(
    matched_exercise: ExerciseCatalogEntry | None,
) -> dict[str, Any]:
    if matched_exercise is None:
        return {}
    return {
        "catalog_exercise_id": matched_exercise.id,
        "name": matched_exercise.name,
        "exercise_type": matched_exercise.exercise_type,
        "movement_pattern": matched_exercise.movement_pattern,
        "primary_muscle_groups": list(matched_exercise.primary_muscle_groups),
    }


def _fit_evidence_items_to_prompt_budget(
    items: Sequence[CoachEvidenceItem],
    *,
    user_id: int,
    as_of_date: str,
    topics: Sequence[str],
    matched_exercise_name: str | None,
    matched_exercise_context: Mapping[str, Any],
    limitations: Sequence[str],
) -> list[CoachEvidenceItem]:
    selected: list[CoachEvidenceItem] = []
    for item in items:
        candidate_items = (*selected, item)
        candidate_pack = CoachEvidencePack(
            pack_version=COACH_EVIDENCE_PACK_VERSION,
            user_id=user_id,
            as_of_date=as_of_date,
            question_topics=tuple(topics),
            matched_exercise_name=matched_exercise_name,
            evidence=candidate_items,
            limitations=tuple(limitations),
            source_services=(),
            confidence="Limited",
            matched_exercise_context=dict(matched_exercise_context),
        )
        serialized = json.dumps(
            candidate_pack.to_prompt_dict(),
            separators=(",", ":"),
            default=str,
        )
        if len(serialized) <= MAX_EVIDENCE_PROMPT_CHARS:
            selected.append(item)
    return selected


def classify_coach_question(question: str) -> tuple[str, ...]:
    normalized = _normalize(question)
    words = set(normalized.split())
    topics: list[str] = []
    has_recovery = bool(words.intersection(_RECOVERY_TERMS))
    has_training = bool(words.intersection(_TRAINING_TERMS))
    has_nutrition = bool(words.intersection(_NUTRITION_TERMS))
    has_body_weight = bool(
        words.intersection(_BODY_WEIGHT_TERMS) or "body weight" in normalized
    )
    broad_phrase = any(phrase in normalized for phrase in _BROAD_PHRASES)
    broad = any(phrase in normalized for phrase in _ALWAYS_BROAD_PHRASES) or (
        broad_phrase
        and not any((has_recovery, has_training, has_nutrition, has_body_weight))
    )
    if broad:
        topics.append("broad")
    if has_recovery:
        topics.append("recovery")
    if has_training:
        topics.append("training")
    if has_nutrition:
        topics.append("nutrition")
    if has_body_weight:
        topics.append("body_weight")
    elif "weight" in words and not words.intersection(
        {
            "load",
            "lift",
            "lifting",
            "exercise",
            "sets",
            "reps",
            "rir",
            "increase",
            "decrease",
            "heavier",
            "lighter",
        }
    ):
        topics.append("body_weight")
    if words.intersection(_PROFILE_TERMS):
        topics.append("profile")
    if _has_equipment_intent(question):
        topics.append("equipment")
    if not topics:
        topics.append("broad")
    if broad:
        for domain in ("recovery", "training", "nutrition", "body_weight", "profile"):
            if domain not in topics:
                topics.append(domain)
    return tuple(topics)


def resolve_referenced_exercise(
    question: str,
    catalog: Sequence[ExerciseCatalogEntry],
) -> ExerciseCatalogEntry | None:
    normalized_question = _normalize(question)
    question_tokens = set(normalized_question.split())
    alias_match = next(
        (
            canonical_name
            for alias, canonical_name in _EXERCISE_NAME_ALIASES.items()
            if alias in question_tokens
        ),
        None,
    )
    if alias_match is not None:
        matched_alias_entry = next(
            (entry for entry in catalog if entry.name == alias_match), None
        )
        if matched_alias_entry is not None:
            return matched_alias_entry
    candidates: list[tuple[float, int, str, ExerciseCatalogEntry]] = []
    for entry in catalog:
        normalized_name = _normalize(entry.name)
        name_tokens = set(normalized_name.split())
        exact = normalized_name in normalized_question
        overlap = len(name_tokens.intersection(question_tokens))
        if not exact and overlap < 2:
            continue
        coverage = overlap / max(1, len(name_tokens))
        score = (10.0 if exact else 0.0) + overlap + coverage
        candidates.append((score, len(name_tokens), normalized_name, entry))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    return candidates[0][3]


def _has_explicit_question_subject(
    question: str,
    catalog: Sequence[ExerciseCatalogEntry],
) -> bool:
    normalized = _normalize(question)
    words = set(normalized.split())
    return bool(
        words.intersection(
            _RECOVERY_TERMS
            | _TRAINING_TERMS
            | _NUTRITION_TERMS
            | _BODY_WEIGHT_TERMS
            | _PROFILE_TERMS
        )
        or _has_equipment_intent(question)
        or any(phrase in normalized for phrase in _BROAD_PHRASES)
        or resolve_referenced_exercise(question, catalog) is not None
    )


def _looks_like_follow_up(question: str) -> bool:
    normalized = _normalize(question)
    words = set(normalized.split())
    return bool(
        words.intersection({"it", "that", "this", "those", "them", "also", "now"})
        or normalized.startswith(("what about", "how about", "and "))
        or normalized.startswith(_ACTION_FOLLOW_UP_PREFIXES)
        or _has_historical_comparison_intent(question)
    )


def _has_explicit_non_training_subject(question: str) -> bool:
    normalized = _normalize(question)
    words = set(normalized.split())
    return bool(
        words.intersection(
            _RECOVERY_TERMS
            | _NUTRITION_TERMS
            | _BODY_WEIGHT_TERMS
            | (_PROFILE_TERMS - {"progress"})
        )
        or _has_equipment_intent(question)
        or "body weight" in normalized
        or any(
            phrase in normalized
            for phrase in ("my training", "my workouts", "training overall")
        )
    )


def _has_equipment_intent(question: str) -> bool:
    normalized = _normalize(question)
    words = set(normalized.split())
    if words.intersection(_EQUIPMENT_TERMS) or any(
        phrase in normalized for phrase in _EQUIPMENT_TERMS if " " in phrase
    ):
        return True
    if "available" not in words:
        return False
    return any(
        (context in words if " " not in context else context in normalized)
        for context in _AVAILABLE_EQUIPMENT_CONTEXT_TERMS
    )


def _has_historical_comparison_intent(question: str) -> bool:
    normalized = _normalize(question)
    words = set(normalized.split())
    return bool(
        words.intersection({"before", "earlier", "previously", "historically"})
        or any(phrase in normalized for phrase in _HISTORICAL_COMPARISON_PHRASES)
    )


def _relevant_insight_domains(topics: set[str]) -> set[str]:
    domains = topics.intersection({"recovery", "training", "nutrition", "body_weight"})
    if len(domains) >= 2:
        domains.add("cross_domain")
    return domains


def _baseline_longitudinal_items(
    insights: Sequence[LongitudinalInsight],
) -> list[CoachEvidenceItem]:
    selected: list[LongitudinalInsight] = []
    for domain in (
        "recovery",
        "training",
        "nutrition",
        "body_weight",
        "cross_domain",
    ):
        match = next((item for item in insights if item.domain == domain), None)
        if match is not None:
            selected.append(match)
        if len(selected) >= MAX_BASELINE_LONGITUDINAL_ITEMS:
            break
    return [_longitudinal_item(insight) for insight in selected]


def _depth_longitudinal_items(
    insights: Sequence[LongitudinalInsight],
    *,
    relevant_domains: set[str],
    broad: bool,
    matched_exercise_name: str | None,
    excluded_references: set[str],
) -> list[CoachEvidenceItem]:
    eligible_domains = (
        {"recovery", "training", "nutrition", "body_weight", "cross_domain"}
        if broad
        else relevant_domains
    )
    selected: list[CoachEvidenceItem] = []
    selected_domains: set[str] = set()
    for insight in insights:
        reference_id = f"insight:{insight.stable_id}"
        if (
            reference_id in excluded_references
            or insight.domain not in eligible_domains
        ):
            continue
        if insight.domain in selected_domains:
            continue
        if (
            matched_exercise_name is not None
            and insight.domain in {"training", "cross_domain"}
            and not _insight_mentions_exercise(insight, matched_exercise_name)
        ):
            continue
        selected.append(_longitudinal_item(insight))
        selected_domains.add(insight.domain)
        if len(selected) >= MAX_DEEP_LONGITUDINAL_ITEMS:
            break
    return selected


def _longitudinal_item(insight: LongitudinalInsight) -> CoachEvidenceItem:
    evidence_values = "; ".join(
        f"{item.label}: {item.value}" for item in insight.evidence[:3]
    )
    fact = f"{insight.title}. {insight.explanation}"
    if evidence_values:
        fact += f" Supporting observations: {evidence_values}."
    return _item(
        f"insight:{insight.stable_id}",
        insight.domain,
        "longitudinal_insight",
        insight.title,
        fact,
        "High" if insight.evidence_strength == "strong" else "Moderate",
        "longitudinal_insight_service",
        insight.observation_window.end_date,
        {
            "window_start": insight.observation_window.start_date,
            "window_end": insight.observation_window.end_date,
            "direction": insight.direction,
            "status": insight.status,
        },
        structured_data={
            "observation_type": insight.insight_type,
            "observation_window": insight.observation_window.to_dict(),
            "comparison_window": (
                insight.comparison_window.to_dict()
                if insight.comparison_window is not None
                else None
            ),
            "measurements": [item.to_dict() for item in insight.evidence],
            "evidence_strength": insight.evidence_strength,
            "coverage": {
                "status": insight.data_coverage.status,
                "observation_count": insight.data_coverage.observation_count,
                "comparison_observation_count": (
                    insight.data_coverage.comparison_observation_count
                ),
                "expected_observation_count": (
                    insight.data_coverage.expected_observation_count
                ),
                "observation_rate": insight.data_coverage.observation_rate,
            },
        },
        synthesis_data=_longitudinal_synthesis_data(insight),
    )


def _insight_mentions_exercise(
    insight: LongitudinalInsight,
    exercise_name: str,
) -> bool:
    evidence_text = " ".join(item.value for item in insight.evidence)
    insight_text = _normalize(f"{insight.title} {insight.explanation} {evidence_text}")
    exercise_tokens = set(_normalize(exercise_name).split())
    return len(exercise_tokens.intersection(insight_text.split())) >= min(
        2, len(exercise_tokens)
    )


def _longitudinal_synthesis_data(
    insight: LongitudinalInsight,
) -> dict[str, Any]:
    recent_window = _synthesis_window(insight.observation_window)
    previous_window = (
        _synthesis_window(insight.comparison_window)
        if insight.comparison_window is not None
        else None
    )
    coverage = {
        "recent_observation_count": insight.data_coverage.observation_count,
        "previous_observation_count": (
            insight.data_coverage.comparison_observation_count
        ),
        "expected_observation_count": (
            insight.data_coverage.expected_observation_count
        ),
        "observation_rate": insight.data_coverage.observation_rate,
    }
    measurements = {item.metric: item for item in insight.evidence}
    if insight.insight_type == "stable_load_rising_effort":
        load_values = _comparison_numbers(measurements.get("comparable_working_weight"))
        rir_values = _comparison_numbers(measurements.get("average_actual_rir"))
        if load_values is not None and rir_values is not None:
            return {
                "exercise": _rising_effort_exercise_name(insight.title),
                "previous_average_load_lb": load_values[0],
                "recent_average_load_lb": load_values[1],
                "previous_average_rir": rir_values[0],
                "recent_average_rir": rir_values[1],
                "previous_window": previous_window,
                "recent_window": recent_window,
                "coverage": coverage,
            }
    return {
        "previous_window": previous_window,
        "recent_window": recent_window,
        "measurements": [
            {
                "metric": item.metric,
                "value": item.value,
                "source_fields": list(item.source_fields),
            }
            for item in insight.evidence
        ],
        "coverage": coverage,
    }


def _synthesis_window(window: Any) -> dict[str, Any]:
    return {
        "start_date": window.start_date,
        "end_date": window.end_date,
        "days": window.days,
        "observation_count": window.observation_count,
    }


def _comparison_numbers(
    evidence: Any | None,
) -> tuple[int | float, int | float] | None:
    if evidence is None:
        return None
    parts = str(evidence.value).split("→")
    if len(parts) != 2:
        return None
    values: list[int | float] = []
    for part in parts:
        match = re.search(r"-?\d+(?:\.\d+)?", part)
        if match is None:
            return None
        value = float(match.group())
        values.append(int(value) if value.is_integer() else value)
    return values[0], values[1]


def _rising_effort_exercise_name(title: str) -> str:
    suffix = " is getting harder at the same load"
    return title[: -len(suffix)] if title.endswith(suffix) else title


def _matching_exercise_history(
    training: WorkoutExerciseHistoryAnalytics | None,
    matched: ExerciseCatalogEntry,
) -> ExerciseHistoryAnalyticsSummary | None:
    if training is None:
        return None
    for exercise in training.exercises:
        if matched.id is not None and exercise.catalog_exercise_id == matched.id:
            return exercise
    matched_tokens = set(_normalize(matched.name).split())
    ranked: list[tuple[int, ExerciseHistoryAnalyticsSummary]] = []
    for exercise in training.exercises:
        overlap = len(
            matched_tokens.intersection(_normalize(exercise.exercise_name).split())
        )
        if overlap >= 2:
            ranked.append((overlap, exercise))
    return max(ranked, key=lambda item: item[0])[1] if ranked else None


def _build_exercise_historical_comparison(
    *,
    user_id: int,
    matched_exercise: ExerciseCatalogEntry,
    end_date: date,
) -> _ExerciseHistoricalComparison | None:
    sessions = load_completed_user_progression_sessions(
        user_id=user_id,
        lookback_days=HISTORICAL_EXERCISE_LOOKBACK_DAYS,
        end_date=end_date,
    )
    matching_sessions = [
        session
        for session in sessions
        if _progression_session_matches_exercise(session, matched_exercise)
    ]
    exposures: list[_ExerciseProgressionExposure] = []
    seen_execution_sessions: set[int] = set()
    for session in matching_sessions:
        if session.workout_execution_session_id in seen_execution_sessions:
            continue
        exposure = _progression_exposure(session)
        if exposure is None:
            continue
        exposures.append(exposure)
        seen_execution_sessions.add(session.workout_execution_session_id)
    exposures.sort(key=lambda item: item.performed_at, reverse=True)
    if len(exposures) < 8:
        return None

    current_phase = _comparison_phase(exposures, offset=0)
    earlier_candidates = [
        _comparison_phase(exposures, offset=offset)
        for offset in range(4, len(exposures) - 3)
    ]
    clear_progression_candidates = [
        phase
        for phase in earlier_candidates
        if _comparison_phase_kind(phase) == "clear_progression"
    ]
    earlier_phase = max(
        clear_progression_candidates,
        key=lambda phase: (
            phase.recent_weight - phase.prior_weight,
            phase.window_end,
        ),
        default=earlier_candidates[0],
    )
    return _ExerciseHistoricalComparison(
        earlier_progression=earlier_phase,
        current_phase=current_phase,
    )


def _progression_session_matches_exercise(
    session: ExerciseProgressionSession,
    matched_exercise: ExerciseCatalogEntry,
) -> bool:
    if (
        matched_exercise.id is not None
        and session.effective_catalog_exercise_id is not None
    ):
        return session.effective_catalog_exercise_id == matched_exercise.id
    return _normalize(session.effective_exercise_name) == _normalize(
        matched_exercise.name
    )


def _progression_exposure(
    session: ExerciseProgressionSession,
) -> _ExerciseProgressionExposure | None:
    if session.performed_at is None:
        return None
    working_weight = comparable_working_weight(session)
    completed_rows = completed_exercise_actual_rows(session)
    rirs = [
        float(row["actual_rir"])
        for row in completed_rows
        if row.get("actual_rir") is not None
    ]
    if (
        working_weight is None
        or not completed_rows
        or len(rirs) != len(completed_rows)
        or any(row.get("actual_reps") is None for row in completed_rows)
    ):
        return None
    return _ExerciseProgressionExposure(
        performed_at=date.fromisoformat(session.performed_at[:10]),
        comparable_working_weight=float(working_weight),
        average_actual_rir=round(mean(rirs), 2),
    )


def _comparison_phase(
    exposures: Sequence[_ExerciseProgressionExposure],
    *,
    offset: int,
) -> _ExerciseComparisonPhase:
    recent = exposures[offset : offset + 2]
    prior = exposures[offset + 2 : offset + 4]
    window = [*recent, *prior]
    return _ExerciseComparisonPhase(
        window_start=min(item.performed_at for item in window).isoformat(),
        window_end=max(item.performed_at for item in window).isoformat(),
        prior_weight=round(mean(item.comparable_working_weight for item in prior), 2),
        recent_weight=round(mean(item.comparable_working_weight for item in recent), 2),
        prior_rir=round(mean(item.average_actual_rir for item in prior), 2),
        recent_rir=round(mean(item.average_actual_rir for item in recent), 2),
    )


def _comparison_phase_kind(phase: _ExerciseComparisonPhase) -> str:
    weight_delta = phase.recent_weight - phase.prior_weight
    rir_delta = phase.recent_rir - phase.prior_rir
    stable_weight_tolerance = max(1.0, phase.prior_weight * 0.01)
    if weight_delta >= max(2.5, phase.prior_weight * 0.02) and rir_delta >= -0.5:
        return "clear_progression"
    if abs(weight_delta) <= stable_weight_tolerance and rir_delta <= -0.75:
        return "rising_effort"
    if abs(weight_delta) <= stable_weight_tolerance and abs(rir_delta) <= 0.5:
        return "stable"
    return "mixed"


def _historical_comparison_items(
    reference_base: str,
    exercise_name: str,
    comparison: _ExerciseHistoricalComparison,
) -> list[CoachEvidenceItem]:
    earlier = comparison.earlier_progression
    current = comparison.current_phase
    return [
        _item(
            f"{reference_base}:historical-phase:{earlier.window_start}:{earlier.window_end}",
            "training",
            "exercise_historical_progression_phase",
            "Earlier exercise progression",
            _comparison_phase_fact(exercise_name, earlier, historical=True),
            "Moderate",
            "workout_progression_history_service",
            earlier.window_end,
            _comparison_phase_metadata(earlier),
            structured_data={
                "exercise_name": exercise_name,
                **_comparison_phase_metadata(earlier),
            },
            synthesis_data={
                "exercise": exercise_name,
                "window_start": earlier.window_start,
                "window_end": earlier.window_end,
                "previous_average_load_lb": earlier.prior_weight,
                "recent_average_load_lb": earlier.recent_weight,
                "previous_average_rir": earlier.prior_rir,
                "recent_average_rir": earlier.recent_rir,
                "session_count": 4,
            },
        ),
        _item(
            f"{reference_base}:current-phase:{current.window_start}:{current.window_end}",
            "training",
            "exercise_current_comparison_phase",
            "Latest exercise comparison",
            _comparison_phase_fact(exercise_name, current, historical=False),
            "Moderate",
            "workout_progression_history_service",
            current.window_end,
            _comparison_phase_metadata(current),
            structured_data={
                "exercise_name": exercise_name,
                **_comparison_phase_metadata(current),
            },
            synthesis_data={
                "exercise": exercise_name,
                "window_start": current.window_start,
                "window_end": current.window_end,
                "previous_average_load_lb": current.prior_weight,
                "recent_average_load_lb": current.recent_weight,
                "previous_average_rir": current.prior_rir,
                "recent_average_rir": current.recent_rir,
                "session_count": 4,
            },
        ),
    ]


def _comparison_phase_fact(
    exercise_name: str,
    phase: _ExerciseComparisonPhase,
    *,
    historical: bool,
) -> str:
    prefix = "An earlier" if historical else "The latest"
    kind = _comparison_phase_kind(phase)
    prior_weight = _format_number(phase.prior_weight)
    recent_weight = _format_number(phase.recent_weight)
    prior_rir = _format_number(phase.prior_rir)
    recent_rir = _format_number(phase.recent_rir)
    window = f"{phase.window_start} to {phase.window_end}"
    if kind == "clear_progression":
        return f"{prefix} four-session comparison for {exercise_name} from {window} showed average comparable working load increasing from {prior_weight} to {recent_weight} lb while average logged RIR moved from {prior_rir} to {recent_rir}, without a meaningful increase in effort."
    if kind == "rising_effort":
        return f"{prefix} four-session comparison for {exercise_name} from {window} showed average comparable working load staying near {recent_weight} lb while average logged RIR fell from {prior_rir} to {recent_rir}. Lower RIR means the sets were logged closer to failure."
    return f"{prefix} four-session comparison for {exercise_name} from {window} showed average comparable working load moving from {prior_weight} to {recent_weight} lb and average logged RIR moving from {prior_rir} to {recent_rir}."


def _comparison_phase_metadata(phase: _ExerciseComparisonPhase) -> dict[str, Any]:
    return {
        "phase_kind": _comparison_phase_kind(phase),
        "window_start": phase.window_start,
        "window_end": phase.window_end,
        "prior_weight_lb": phase.prior_weight,
        "recent_weight_lb": phase.recent_weight,
        "prior_average_rir": phase.prior_rir,
        "recent_average_rir": phase.recent_rir,
        "session_count": 4,
    }


def _exercise_history_items(
    reference_base: str,
    exercise: ExerciseHistoryAnalyticsSummary,
) -> list[CoachEvidenceItem]:
    items = [
        _item(
            f"{reference_base}:history",
            "training",
            "exercise_history",
            "Completed exercise history",
            (
                f"{exercise.exercise_name} has {exercise.completed_session_count} completed sessions in the bounded history. "
                f"The latest was {exercise.last_performed_at}: {exercise.latest_completed_session_summary}"
            ),
            "High" if exercise.logging_quality == "complete" else "Moderate",
            "workout_exercise_history_analytics_service",
            exercise.last_performed_at,
            structured_data={
                "exercise_name": exercise.exercise_name,
                "completed_session_count": exercise.completed_session_count,
                "logging_quality": exercise.logging_quality,
                "latest_session": (
                    {
                        "performed_at": exercise.recent_sessions[0].performed_at,
                        "completed_set_count": (
                            exercise.recent_sessions[0].completed_set_count
                        ),
                        "planned_set_count": (
                            exercise.recent_sessions[0].planned_set_count
                        ),
                        "comparable_working_weight_lb": (
                            exercise.recent_sessions[0].comparable_working_weight
                        ),
                        "average_actual_rir": (
                            exercise.recent_sessions[0].average_actual_rir
                        ),
                    }
                    if exercise.recent_sessions
                    else None
                ),
            },
            synthesis_data={
                "exercise": exercise.exercise_name,
                "completed_session_count": exercise.completed_session_count,
                "latest_session": (
                    {
                        "performed_at": exercise.recent_sessions[0].performed_at,
                        "completed_set_count": (
                            exercise.recent_sessions[0].completed_set_count
                        ),
                        "planned_set_count": (
                            exercise.recent_sessions[0].planned_set_count
                        ),
                        "comparable_working_weight_lb": (
                            exercise.recent_sessions[0].comparable_working_weight
                        ),
                        "average_actual_rir": (
                            exercise.recent_sessions[0].average_actual_rir
                        ),
                    }
                    if exercise.recent_sessions
                    else None
                ),
                **(
                    {"logging_quality": exercise.logging_quality}
                    if exercise.logging_quality != "complete"
                    else {}
                ),
            },
        )
    ]
    trend = exercise.recent_working_load_trend
    if trend.status != "insufficient_data":
        change = (
            f" by {trend.absolute_change_lb:g} lb" if trend.absolute_change_lb else ""
        )
        items.append(
            _item(
                f"{reference_base}:load-trend",
                "training",
                "exercise_load_trend",
                "Recent working-load trend",
                (
                    f"Comparable working load for {exercise.exercise_name} was {trend.status.replace('_', ' ')}{change} "
                    f"across {trend.qualifying_session_count} qualifying sessions (latest {trend.latest_comparable_working_weight:g} lb, "
                    f"comparison {trend.comparison_working_weight:g} lb)."
                ),
                "Moderate",
                "workout_exercise_history_analytics_service",
                exercise.last_performed_at,
                structured_data={
                    "exercise_name": exercise.exercise_name,
                    "status": trend.status,
                    "absolute_change_lb": trend.absolute_change_lb,
                    "qualifying_session_count": trend.qualifying_session_count,
                    "latest_comparable_working_weight_lb": (
                        trend.latest_comparable_working_weight
                    ),
                    "comparison_working_weight_lb": (trend.comparison_working_weight),
                },
                synthesis_data={
                    "exercise": exercise.exercise_name,
                    "latest_comparable_working_weight_lb": (
                        trend.latest_comparable_working_weight
                    ),
                    "comparison_working_weight_lb": (trend.comparison_working_weight),
                    "absolute_change_lb": trend.absolute_change_lb,
                    "qualifying_session_count": trend.qualifying_session_count,
                },
            )
        )
    rir_sessions = [
        session
        for session in exercise.recent_sessions
        if session.average_actual_rir is not None
    ]
    if len(rir_sessions) >= 2:
        latest = rir_sessions[0]
        comparison = rir_sessions[-1]
        items.append(
            _item(
                f"{reference_base}:effort-trend",
                "training",
                "exercise_effort_trend",
                "Recent logged effort",
                (
                    f"Average logged RIR for {exercise.exercise_name} was {latest.average_actual_rir:g} on {latest.performed_at} "
                    f"versus {comparison.average_actual_rir:g} on {comparison.performed_at}. Lower RIR means the sets were logged closer to failure."
                ),
                "Moderate",
                "workout_exercise_history_analytics_service",
                latest.performed_at,
                structured_data={
                    "observation_type": "logged_effort_comparison",
                    "exercise_name": exercise.exercise_name,
                    "latest": {
                        "performed_at": latest.performed_at,
                        "comparable_working_weight_lb": (
                            latest.comparable_working_weight
                        ),
                        "average_actual_rir": latest.average_actual_rir,
                    },
                    "comparison": {
                        "performed_at": comparison.performed_at,
                        "comparable_working_weight_lb": (
                            comparison.comparable_working_weight
                        ),
                        "average_actual_rir": comparison.average_actual_rir,
                    },
                },
                synthesis_data={
                    "exercise": exercise.exercise_name,
                    "recent": {
                        "performed_at": latest.performed_at,
                        "comparable_working_weight_lb": (
                            latest.comparable_working_weight
                        ),
                        "average_actual_rir": latest.average_actual_rir,
                    },
                    "previous": {
                        "performed_at": comparison.performed_at,
                        "comparable_working_weight_lb": (
                            comparison.comparable_working_weight
                        ),
                        "average_actual_rir": comparison.average_actual_rir,
                    },
                },
            )
        )
    recommendation = exercise.progression_recommendation
    if recommendation.evidence_session_count > 0:
        items.append(
            _item(
                f"{reference_base}:progression-decision",
                "training",
                "deterministic_progression_decision",
                recommendation.headline,
                recommendation.target_guidance,
                _confidence(recommendation.confidence),
                "workout_progression_decision_service",
                exercise.last_performed_at,
                {"decision": recommendation.decision},
                structured_data={
                    "decision": recommendation.decision,
                    "evidence_session_count": recommendation.evidence_session_count,
                    "confidence": recommendation.confidence,
                },
                synthesis_data={
                    "evidence_session_count": recommendation.evidence_session_count,
                },
            )
        )
    return items


def _recovery_items(recovery: Any) -> list[CoachEvidenceItem]:
    items: list[CoachEvidenceItem] = []
    current = getattr(recovery, "current_day", None)
    if current is not None:
        values = []
        for label, value, suffix in (
            ("sleep", current.sleep_hours, " hours"),
            ("sleep quality", current.sleep_quality, "/5"),
            ("energy", current.energy_level, "/10"),
            ("soreness", current.soreness_level, "/10"),
            ("stress", current.stress_level, "/5"),
            ("training motivation", current.training_motivation, "/5"),
        ):
            if value is not None:
                values.append(f"{label} {value:g}{suffix}")
        if current.pain_concern is not None:
            pain = f"pain concern {current.pain_concern}"
            if current.pain_area:
                pain += f" ({_humanize(current.pain_area)})"
            values.append(pain)
        if values:
            items.append(
                _item(
                    f"recovery:day:{current.date}",
                    "recovery",
                    "current_recovery_checkin",
                    "Latest recovery check-in",
                    f"On {current.date}, the check-in recorded "
                    + ", ".join(values)
                    + ".",
                    _confidence(getattr(recovery, "confidence", "Limited")),
                    "recovery_intelligence_v2_service",
                    current.date,
                    structured_data={
                        "date": current.date,
                        "sleep_hours": current.sleep_hours,
                        "sleep_quality": current.sleep_quality,
                        "energy_level": current.energy_level,
                        "soreness_level": current.soreness_level,
                        "stress_level": current.stress_level,
                        "training_motivation": current.training_motivation,
                        "pain_concern": current.pain_concern,
                        "pain_area": current.pain_area,
                        "data_quality_status": getattr(
                            current, "data_quality_status", None
                        ),
                    },
                    synthesis_data=_current_recovery_synthesis_data(current),
                )
            )

    for comparison in (
        getattr(recovery, "recent_vs_baseline", None),
        getattr(recovery, "recent_vs_prior", None),
    ):
        if (
            comparison is None
            or getattr(comparison, "confidence", "Limited") == "Limited"
        ):
            continue
        comparison_name = str(comparison.comparison_name)
        data = {
            "observation_type": "recovery_window_comparison",
            "comparison_name": comparison_name,
            "recent_window_days": comparison.recent_window_days,
            "comparison_window_days": comparison.comparison_window_days,
            "sleep_hours_delta": comparison.sleep_delta,
            "energy_level_delta": comparison.energy_delta,
            "soreness_level_delta": comparison.soreness_delta,
            "body_weight_lb_delta": comparison.body_weight_delta,
            "trend_direction": comparison.trend_direction,
            "confidence": comparison.confidence,
        }
        items.append(
            _item(
                f"recovery:comparison:{comparison_name}:{recovery.target_date}",
                "recovery",
                "recovery_window_comparison",
                "Recovery window comparison",
                (
                    f"The {comparison_name.replace('_', ' ')} recovery comparison "
                    f"covers {comparison.recent_window_days} recent days and "
                    f"{comparison.comparison_window_days} comparison days."
                ),
                _confidence(comparison.confidence),
                "recovery_intelligence_v2_service",
                recovery.target_date,
                structured_data=data,
                synthesis_data={
                    "comparison_name": comparison_name,
                    "recent_window_days": comparison.recent_window_days,
                    "comparison_window_days": comparison.comparison_window_days,
                    "sleep_hours_delta": comparison.sleep_delta,
                    "energy_level_delta": comparison.energy_delta,
                    "soreness_level_delta": comparison.soreness_delta,
                    "body_weight_lb_delta": comparison.body_weight_delta,
                },
            )
        )
    return items


def _current_recovery_synthesis_data(current: Any) -> dict[str, Any]:
    data = {
        "date": current.date,
        "sleep_hours": current.sleep_hours,
        "sleep_quality": _scaled_subjective_recovery_value(
            "sleep_quality", current.sleep_quality
        ),
        "energy_level": _scaled_subjective_recovery_value(
            "energy_level", current.energy_level
        ),
        "soreness_level": _scaled_subjective_recovery_value(
            "soreness_level", current.soreness_level
        ),
        "stress_level": _scaled_subjective_recovery_value(
            "stress_level", current.stress_level
        ),
        "training_motivation": _scaled_subjective_recovery_value(
            "training_motivation", current.training_motivation
        ),
        "pain_concern": current.pain_concern,
        "pain_area": current.pain_area,
    }
    data_quality_status = getattr(current, "data_quality_status", None)
    if data_quality_status in {"missing", "limited", "partial"}:
        data["data_quality_status"] = data_quality_status
    return data


def _scaled_subjective_recovery_value(
    field_name: str, value: int | float | None
) -> dict[str, int | float] | None:
    if value is None:
        return None
    scale_min, scale_max = _SUBJECTIVE_RECOVERY_SCALES[field_name]
    return {
        "value": value,
        "scale_min": scale_min,
        "scale_max": scale_max,
    }


def _nutrition_items(
    nutrition: Any, *, include_weight: bool
) -> list[CoachEvidenceItem]:
    items: list[CoachEvidenceItem] = []
    if nutrition.logged_day_count > 0:
        intake = nutrition.intake_trend_summary
        items.append(
            _item(
                f"nutrition:logging:{nutrition.start_date}:{nutrition.end_date}",
                "nutrition",
                "nutrition_logging_quality",
                "Nutrition logging coverage",
                (
                    f"From {nutrition.start_date} through {nutrition.end_date}, nutrition was logged on "
                    f"{nutrition.logged_day_count} of {nutrition.window_days} days; {nutrition.complete_logging_day_count} days were complete "
                    f"and {nutrition.partial_logging_day_count} were partial. Logging consistency was {intake.logging_consistency_status.replace('_', ' ')}."
                ),
                _confidence(intake.confidence),
                "nutrition_trend_service",
                nutrition.end_date,
                structured_data={
                    "window_start": nutrition.start_date,
                    "window_end": nutrition.end_date,
                    "window_days": nutrition.window_days,
                    "logged_day_count": nutrition.logged_day_count,
                    "complete_logging_day_count": (
                        nutrition.complete_logging_day_count
                    ),
                    "partial_logging_day_count": (nutrition.partial_logging_day_count),
                    "logging_consistency_status": (intake.logging_consistency_status),
                },
                synthesis_data={
                    "window_start": nutrition.start_date,
                    "window_end": nutrition.end_date,
                    "window_days": nutrition.window_days,
                    "logged_day_count": nutrition.logged_day_count,
                    "complete_logging_day_count": (
                        nutrition.complete_logging_day_count
                    ),
                    "partial_logging_day_count": (nutrition.partial_logging_day_count),
                },
            )
        )
        averages = []
        for label, value, suffix in (
            ("calories", intake.average_calories, " kcal"),
            ("protein", intake.average_protein_g, " g"),
            ("carbohydrate", intake.average_carbohydrate_g, " g"),
            ("fat", intake.average_fat_g, " g"),
        ):
            if value is not None:
                averages.append(f"{label} {value:g}{suffix}")
        if averages:
            items.append(
                _item(
                    f"nutrition:averages:{nutrition.start_date}:{nutrition.end_date}",
                    "nutrition",
                    "nutrition_averages",
                    "Logged nutrition averages",
                    "Across eligible logged days, the averages were "
                    + ", ".join(averages)
                    + ".",
                    _confidence(intake.confidence),
                    "nutrition_trend_service",
                    nutrition.end_date,
                    structured_data={
                        "window_start": nutrition.start_date,
                        "window_end": nutrition.end_date,
                        "average_calories": intake.average_calories,
                        "average_protein_g": intake.average_protein_g,
                        "average_carbohydrate_g": (intake.average_carbohydrate_g),
                        "average_fat_g": intake.average_fat_g,
                    },
                )
            )
    if include_weight:
        weight = nutrition.bodyweight_trend_summary
        if weight.weigh_in_count >= 2 and weight.trend_direction != "unavailable":
            fact = (
                f"The {nutrition.window_days}-day window contains {weight.weigh_in_count} weigh-ins. "
                f"Body weight was {weight.trend_direction.replace('_', ' ')}"
            )
            if weight.start_weight_lb is not None and weight.end_weight_lb is not None:
                fact += f" from {weight.start_weight_lb:g} lb to {weight.end_weight_lb:g} lb"
            if weight.weekly_rate_lb is not None:
                fact += f", at an estimated {weight.weekly_rate_lb:g} lb per week"
            fact += "."
            items.append(
                _item(
                    f"body-weight:trend:{nutrition.start_date}:{nutrition.end_date}",
                    "body_weight",
                    "body_weight_trend",
                    "Body-weight trend",
                    fact,
                    _confidence(weight.confidence),
                    "nutrition_trend_service",
                    nutrition.end_date,
                    structured_data={
                        "window_start": nutrition.start_date,
                        "window_end": nutrition.end_date,
                        "window_days": nutrition.window_days,
                        "weigh_in_count": weight.weigh_in_count,
                        "trend_direction": weight.trend_direction,
                        "start_weight_lb": weight.start_weight_lb,
                        "end_weight_lb": weight.end_weight_lb,
                        "weekly_rate_lb": weight.weekly_rate_lb,
                    },
                    synthesis_data={
                        "window_start": nutrition.start_date,
                        "window_end": nutrition.end_date,
                        "window_days": nutrition.window_days,
                        "weigh_in_count": weight.weigh_in_count,
                        "start_weight_lb": weight.start_weight_lb,
                        "end_weight_lb": weight.end_weight_lb,
                        "weekly_rate_lb": weight.weekly_rate_lb,
                    },
                )
            )
    return items


def _item(
    reference_id: str,
    domain: str,
    evidence_type: str,
    label: str,
    fact: str,
    confidence: CoachConfidence,
    source: str,
    observed_at: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    structured_data: Mapping[str, Any] | None = None,
    synthesis_data: Mapping[str, Any] | None = None,
) -> CoachEvidenceItem:
    return CoachEvidenceItem(
        reference_id=reference_id,
        domain=domain,
        evidence_type=evidence_type,
        label=label,
        fact=" ".join(fact.split()),
        confidence=confidence,
        source=source,
        observed_at=observed_at,
        metadata=dict(metadata or {}),
        structured_data=dict(structured_data or {}),
        synthesis_data=dict(synthesis_data or {}),
    )


def _pack_confidence(items: Sequence[CoachEvidenceItem]) -> CoachConfidence:
    if not items:
        return "Limited"
    values = [_CONFIDENCE_ORDER[item.confidence] for item in items]
    if len(items) == 1:
        value = min(values[0], _CONFIDENCE_ORDER["Low"])
    else:
        value = min(values)
    return next(
        confidence for confidence, rank in _CONFIDENCE_ORDER.items() if rank == value
    )  # type: ignore[return-value]


def _confidence(value: str) -> CoachConfidence:
    normalized = value.strip().title() if isinstance(value, str) else "Limited"
    return normalized if normalized in _CONFIDENCE_ORDER else "Limited"  # type: ignore[return-value]


def _dedupe_items(items: Iterable[CoachEvidenceItem]) -> list[CoachEvidenceItem]:
    seen: set[str] = set()
    result: list[CoachEvidenceItem] = []
    for item in items:
        if item.reference_id not in seen:
            result.append(item)
            seen.add(item.reference_id)
    return result


def _dedupe_text(values: Iterable[str]) -> list[str]:
    return list(
        dict.fromkeys(" ".join(value.split()) for value in values if value.strip())
    )


def _clean_value(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ")


def _format_number(value: float) -> str:
    return f"{value:g}"


def _token(value: str) -> str:
    return "-".join(_normalize(value).split())


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _resolve_date(value: str | date | None) -> date:
    if value is None:
        return date.today()
    return value if isinstance(value, date) else date.fromisoformat(value)
