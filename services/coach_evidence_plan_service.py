from __future__ import annotations

import calendar
import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, timedelta

from models.coach_models import (
    CoachConversationTurn,
    CoachEvidenceComparisonMode,
    CoachEvidencePlan,
    CoachEvidencePlanLimitation,
    CoachEvidenceWindow,
)

COACH_EVIDENCE_PLAN_VERSION = "coach_evidence_plan_v1"
MAX_PLANNED_HISTORY_DAYS = 365

_DOMAIN_ORDER = ("training", "recovery", "nutrition", "body_weight", "profile")
_HISTORICAL_DOMAINS = ("training", "recovery", "nutrition", "body_weight")
_FOLLOW_UP_PREFIXES = (
    "and ",
    "what about",
    "how about",
    "what happened",
    "how did",
    "was it",
    "were they",
)
_HISTORICAL_TERMS = {
    "ago",
    "before",
    "earlier",
    "historically",
    "history",
    "past",
    "previous",
    "previously",
    "since",
}
_MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)"
)
_DATE_TOKEN_PATTERN = (
    rf"(?:\d{{4}}-\d{{1,2}}-\d{{1,2}}|{_MONTH_PATTERN}\s+\d{{1,2}}(?:st|nd|rd|th)?"
    rf"(?:,?\s+\d{{4}})?|\d{{1,2}}\s+{_MONTH_PATTERN}(?:\s+\d{{4}})?)"
)


def build_coach_evidence_plan(
    *,
    question: str,
    as_of_date: date,
    question_topics: Sequence[str],
    conversation_context: Sequence[CoachConversationTurn] = (),
    subject: str | None = None,
    subject_inherited: bool = False,
) -> CoachEvidencePlan:
    """Create a deterministic, provider-independent historical retrieval plan."""

    normalized = _normalize(question)
    requested_domains = _requested_domains(normalized, question_topics)
    current_horizon = _parse_horizon(question, as_of_date)
    comparison_mode = _comparison_mode(normalized)
    inherited_horizon = False

    prior_user_turns = [
        turn.content for turn in reversed(conversation_context) if turn.role == "user"
    ]
    if current_horizon is None and _can_inherit_context(normalized):
        for prior_question in prior_user_turns:
            prior_horizon = _parse_horizon(prior_question, as_of_date)
            if prior_horizon is None:
                continue
            current_horizon = prior_horizon
            inherited_horizon = True
            if comparison_mode == "none":
                comparison_mode = _comparison_mode(_normalize(prior_question))
            break

    if current_horizon is None and comparison_mode != "none":
        current_horizon = _default_historical_horizon(as_of_date)
    if current_horizon is None and _has_historical_intent(normalized):
        current_horizon = _default_historical_horizon(as_of_date)

    if current_horizon is None:
        return CoachEvidencePlan(
            plan_version=COACH_EVIDENCE_PLAN_VERSION,
            requested_domains=requested_domains,
            subject=subject,
            horizon_kind="recent_baseline",
            requested_start_date=None,
            requested_end_date=None,
            retrieval_start_date=None,
            retrieval_end_date=None,
            comparison_mode="none",
            historical_depth="baseline",
            windows=(),
            inherited_subject=subject_inherited,
            inherited_horizon=False,
        )

    horizon_kind, requested_start, requested_end = current_horizon
    plan_limitations: list[CoachEvidencePlanLimitation] = []
    retrieval_end = min(requested_end, as_of_date)
    if requested_end > as_of_date:
        plan_limitations.append(
            CoachEvidencePlanLimitation(
                code="future_dates_excluded",
                message=(
                    "The requested range extended beyond the as-of date; future dates "
                    "were excluded from retrieval."
                ),
                requested_start_date=requested_start.isoformat(),
                requested_end_date=requested_end.isoformat(),
                available_end_date=as_of_date.isoformat(),
            )
        )
    earliest_supported = retrieval_end - timedelta(days=MAX_PLANNED_HISTORY_DAYS - 1)
    retrieval_start = max(requested_start, earliest_supported)
    if requested_start < retrieval_start:
        plan_limitations.append(
            CoachEvidencePlanLimitation(
                code="requested_horizon_exceeds_v1_limit",
                message=(
                    "Evidence planning v1 retrieves at most 365 days; the earlier "
                    "part of the requested range was not retrieved."
                ),
                requested_start_date=requested_start.isoformat(),
                requested_end_date=requested_end.isoformat(),
                available_start_date=retrieval_start.isoformat(),
                available_end_date=retrieval_end.isoformat(),
            )
        )

    if retrieval_start > retrieval_end:
        plan_limitations.append(
            CoachEvidencePlanLimitation(
                code="invalid_requested_range",
                message="The requested date range does not include any date on or before the as-of date.",
                requested_start_date=requested_start.isoformat(),
                requested_end_date=requested_end.isoformat(),
            )
        )
        return CoachEvidencePlan(
            plan_version=COACH_EVIDENCE_PLAN_VERSION,
            requested_domains=requested_domains,
            subject=subject,
            horizon_kind=horizon_kind,
            requested_start_date=requested_start.isoformat(),
            requested_end_date=requested_end.isoformat(),
            retrieval_start_date=None,
            retrieval_end_date=None,
            comparison_mode=comparison_mode,
            historical_depth="baseline",
            windows=(),
            inherited_subject=subject_inherited,
            inherited_horizon=inherited_horizon,
            limitations=tuple(plan_limitations),
        )

    windows = _planned_windows(
        normalized=normalized,
        start=retrieval_start,
        end=retrieval_end,
        comparison_mode=comparison_mode,
    )
    retrieval_days = (retrieval_end - retrieval_start).days + 1
    historical_depth = "extended" if retrieval_days > 90 else "window"
    return CoachEvidencePlan(
        plan_version=COACH_EVIDENCE_PLAN_VERSION,
        requested_domains=requested_domains,
        subject=subject,
        horizon_kind=horizon_kind,
        requested_start_date=requested_start.isoformat(),
        requested_end_date=requested_end.isoformat(),
        retrieval_start_date=retrieval_start.isoformat(),
        retrieval_end_date=retrieval_end.isoformat(),
        comparison_mode=comparison_mode,
        historical_depth=historical_depth,
        windows=windows,
        presentation_windows=_presentation_windows(
            horizon_kind=horizon_kind,
            start=retrieval_start,
            end=retrieval_end,
            analysis_windows=windows,
        ),
        inherited_subject=subject_inherited,
        inherited_horizon=inherited_horizon,
        limitations=tuple(plan_limitations),
    )


def add_plan_limitations(
    plan: CoachEvidencePlan,
    limitations: Sequence[CoachEvidencePlanLimitation],
) -> CoachEvidencePlan:
    existing = set(plan.limitations)
    additions = [item for item in limitations if item not in existing]
    return replace(plan, limitations=(*plan.limitations, *additions))


def _requested_domains(
    normalized: str,
    question_topics: Sequence[str],
) -> tuple[str, ...]:
    topics = set(question_topics)
    domains = [domain for domain in _DOMAIN_ORDER if domain in topics]
    broad_historical = any(
        phrase in normalized
        for phrase in (
            "biggest change",
            "what changed when",
            "patterns keep repeating",
            "pattern keeps repeating",
            "progress started stalling",
            "progress stalled",
            "progress plateau",
        )
    )
    if "deload" in normalized:
        domains = ["training", "recovery"]
    elif "broad" in topics or broad_historical:
        domains = list(_HISTORICAL_DOMAINS)
    if "fat loss" in normalized or "fat-loss" in normalized:
        domains.extend(("nutrition", "body_weight", "training", "recovery"))
    if "weight" in normalized and any(
        word in normalized for word in ("dropping", "dropped", "loss")
    ):
        domains.extend(("body_weight", "nutrition", "training", "recovery"))
    return tuple(dict.fromkeys(domain for domain in _DOMAIN_ORDER if domain in domains))


def _comparison_mode(normalized: str) -> CoachEvidenceComparisonMode:
    if "deload" in normalized or "respond to" in normalized:
        return "event_response"
    if "when was" in normalized and any(
        word in normalized for word in ("best", "strongest", "highest")
    ):
        return "best_period"
    if any(
        phrase in normalized
        for phrase in (
            "biggest change",
            "what changed when",
            "started stalling",
            "started dropping",
            "started rising",
            "turning point",
        )
    ):
        return "change_points"
    if any(
        phrase in normalized
        for phrase in (
            "patterns keep repeating",
            "pattern keeps repeating",
            "patterns repeat",
            "recurring pattern",
            "keep happening",
            "keep repeating",
        )
    ):
        return "recurring_patterns"
    if any(
        phrase in normalized
        for phrase in (
            "versus",
            " vs ",
            "compare ",
            "compared with",
            "compared to",
            "than the week before",
        )
    ) or ("ago" in normalized and "than" in normalized):
        return "adjacent_periods"
    words = set(normalized.split())
    if words.intersection({"ago", "before", "earlier", "previously"}) or any(
        phrase in normalized
        for phrase in ("over time", "what happened when", "how did i respond")
    ):
        return "earlier_vs_recent"
    return "none"


def _parse_horizon(
    question: str,
    as_of_date: date,
) -> tuple[str, date, date] | None:
    normalized = _normalize(question)
    explicit = _explicit_date_range(question, as_of_date)
    if explicit is not None:
        return ("explicit_date_range", explicit[0], explicit[1])

    since = re.search(rf"\bsince\s+({_DATE_TOKEN_PATTERN})", question, re.IGNORECASE)
    if since is not None:
        parsed = _parse_natural_date(since.group(1), as_of_date)
        if parsed is not None:
            return ("since_date", parsed, as_of_date)

    if "two weeks ago" in normalized and any(
        word in normalized for word in ("now", "today", "than")
    ):
        return ("two_weeks_ago_vs_now", as_of_date - timedelta(days=20), as_of_date)
    if "last week" in normalized and "week before" in normalized:
        return ("week_over_week", as_of_date - timedelta(days=13), as_of_date)

    day_match = re.search(r"\b(?:last|past)\s+(\d{1,3})\s+days?\b", normalized)
    if day_match is not None:
        period_days = max(1, int(day_match.group(1)))
        comparison_requested = any(
            phrase in normalized
            for phrase in (
                "compare ",
                "compared with",
                "compared to",
                "versus",
                " vs ",
            )
        )
        retrieval_days = period_days * 2 if comparison_requested else period_days
        kind = (
            f"last_{period_days}_days_vs_previous_{period_days}"
            if comparison_requested
            else f"last_{period_days}_days"
        )
        return (
            kind,
            as_of_date - timedelta(days=retrieval_days - 1),
            as_of_date,
        )

    if any(phrase in normalized for phrase in ("three months", "3 months", "quarter")):
        return ("last_90_days", as_of_date - timedelta(days=89), as_of_date)
    if any(
        phrase in normalized
        for phrase in ("last year", "past year", "one year", "12 months", "annual")
    ):
        return ("last_year", as_of_date - timedelta(days=364), as_of_date)
    if any(phrase in normalized for phrase in ("six months", "6 months", "half year")):
        return (
            "last_6_months",
            _subtract_months(as_of_date, 6) + timedelta(days=1),
            as_of_date,
        )
    if any(phrase in normalized for phrase in ("three month", "90 day")):
        return ("last_90_days", as_of_date - timedelta(days=89), as_of_date)
    if any(phrase in normalized for phrase in ("last month", "past month", "28 days")):
        return ("last_28_days", as_of_date - timedelta(days=27), as_of_date)
    if "14 days" in normalized or "two weeks" in normalized:
        return ("last_14_days", as_of_date - timedelta(days=13), as_of_date)
    if "last week" in normalized or "past week" in normalized:
        return ("last_7_days", as_of_date - timedelta(days=6), as_of_date)
    return None


def _explicit_date_range(question: str, as_of_date: date) -> tuple[date, date] | None:
    match = re.search(
        rf"\b(?:from\s+)?({_DATE_TOKEN_PATTERN})\s+(?:through|thru|to|until|-)\s+({_DATE_TOKEN_PATTERN})",
        question,
        re.IGNORECASE,
    )
    if match is None:
        return None
    start = _parse_natural_date(match.group(1), as_of_date)
    end = _parse_natural_date(match.group(2), as_of_date)
    if start is None or end is None:
        return None
    return (start, end) if start <= end else (end, start)


def _parse_natural_date(value: str, as_of_date: date) -> date | None:
    compact = re.sub(r"(?<=\d)(?:st|nd|rd|th)\b", "", value.strip(), flags=re.I)
    compact = re.sub(r"\s+", " ", compact)
    for pattern in (
        "%Y-%m-%d",
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(compact, pattern).date()
        except ValueError:
            continue
    for pattern in ("%B %d", "%b %d", "%d %B", "%d %b"):
        try:
            parsed = datetime.strptime(compact, pattern)
        except ValueError:
            continue
        candidate = date(as_of_date.year, parsed.month, parsed.day)
        return (
            candidate
            if candidate <= as_of_date
            else candidate.replace(year=candidate.year - 1)
        )
    return None


def _default_historical_horizon(as_of_date: date) -> tuple[str, date, date]:
    return ("bounded_history", as_of_date - timedelta(days=364), as_of_date)


def _planned_windows(
    *,
    normalized: str,
    start: date,
    end: date,
    comparison_mode: CoachEvidenceComparisonMode,
) -> tuple[CoachEvidenceWindow, ...]:
    if "two weeks ago" in normalized and comparison_mode == "adjacent_periods":
        return (
            _window(
                "two_weeks_ago",
                end - timedelta(days=20),
                end - timedelta(days=14),
                "comparison",
            ),
            _window("current_week", end - timedelta(days=6), end, "recent"),
        )
    days = (end - start).days + 1
    if comparison_mode == "adjacent_periods" and days in {14, 28, 56}:
        period_days = days // 2
        previous_end = end - timedelta(days=period_days)
        return (
            _window("previous_period", start, previous_end, "comparison"),
            _window(
                "recent_period",
                previous_end + timedelta(days=1),
                end,
                "recent",
            ),
        )
    segment_count = _segment_count(days)
    if segment_count == 1:
        return (_window("requested_period", start, end, "requested"),)
    windows: list[CoachEvidenceWindow] = []
    remaining_start = start
    for index in range(segment_count):
        remaining_days = (end - remaining_start).days + 1
        remaining_segments = segment_count - index
        segment_days = max(
            1, (remaining_days + remaining_segments - 1) // remaining_segments
        )
        segment_end = min(end, remaining_start + timedelta(days=segment_days - 1))
        windows.append(
            _window(
                f"segment_{index + 1}",
                remaining_start,
                segment_end,
                "historical_segment",
            )
        )
        remaining_start = segment_end + timedelta(days=1)
    return tuple(windows)


def _segment_count(days: int) -> int:
    if days <= 31:
        return 1
    if days <= 100:
        return 3
    if days <= 200:
        return 6
    return 9


def _presentation_windows(
    *,
    horizon_kind: str,
    start: date,
    end: date,
    analysis_windows: Sequence[CoachEvidenceWindow],
) -> tuple[CoachEvidenceWindow, ...]:
    days = (end - start).days + 1
    if (
        horizon_kind
        in {
            "week_over_week",
            "two_weeks_ago_vs_now",
        }
        or "_vs_previous_" in horizon_kind
    ):
        return tuple(_humanized_analysis_window(window) for window in analysis_windows)
    if days >= 60:
        return _calendar_month_windows(start, end)
    period_days = 7 if days <= 14 else 14
    return _rolling_presentation_windows(start, end, period_days=period_days)


def _calendar_month_windows(start: date, end: date) -> tuple[CoachEvidenceWindow, ...]:
    windows: list[CoachEvidenceWindow] = []
    cursor = start
    while cursor <= end:
        month_days = calendar.monthrange(cursor.year, cursor.month)[1]
        calendar_start = cursor.replace(day=1)
        calendar_end = cursor.replace(day=month_days)
        period_end = min(end, calendar_end)
        is_partial = cursor != calendar_start or period_end != calendar_end
        windows.append(
            CoachEvidenceWindow(
                label=_calendar_period_label(cursor, period_end, is_partial),
                start_date=cursor.isoformat(),
                end_date=period_end.isoformat(),
                role=("partial_calendar_month" if is_partial else "calendar_month"),
                period_kind="calendar_month",
                expected_days=month_days,
                is_partial_period=is_partial,
            )
        )
        cursor = period_end + timedelta(days=1)
    return tuple(windows)


def _rolling_presentation_windows(
    start: date,
    end: date,
    *,
    period_days: int,
) -> tuple[CoachEvidenceWindow, ...]:
    windows: list[CoachEvidenceWindow] = []
    cursor = start
    while cursor <= end:
        period_end = min(end, cursor + timedelta(days=period_days - 1))
        actual_days = (period_end - cursor).days + 1
        is_partial = actual_days != period_days
        windows.append(
            CoachEvidenceWindow(
                label=_rolling_period_label(
                    cursor,
                    period_end,
                    period_days=period_days,
                    is_partial=is_partial,
                ),
                start_date=cursor.isoformat(),
                end_date=period_end.isoformat(),
                role=("partial_rolling_period" if is_partial else "rolling_period"),
                period_kind=("week" if period_days == 7 else "two_week_period"),
                expected_days=period_days,
                is_partial_period=is_partial,
            )
        )
        cursor = period_end + timedelta(days=1)
    return tuple(windows)


def _humanized_analysis_window(window: CoachEvidenceWindow) -> CoachEvidenceWindow:
    start = date.fromisoformat(window.start_date)
    end = date.fromisoformat(window.end_date)
    return CoachEvidenceWindow(
        label=_rolling_period_label(
            start,
            end,
            period_days=window.days,
            is_partial=False,
        ),
        start_date=window.start_date,
        end_date=window.end_date,
        role=window.role,
        period_kind=("week" if window.days == 7 else "dated_period"),
        expected_days=window.days,
        is_partial_period=False,
    )


def _calendar_period_label(start: date, end: date, is_partial: bool) -> str:
    if not is_partial:
        return start.strftime("%B %Y")
    return f"{_human_date_range(start, end)} (partial month)"


def _rolling_period_label(
    start: date,
    end: date,
    *,
    period_days: int,
    is_partial: bool,
) -> str:
    if period_days == 7 and not is_partial:
        return f"the week of {_human_date_range(start, end)}"
    if period_days == 14 and not is_partial:
        return f"the two weeks ending {end.strftime('%B')} {end.day}, {end.year}"
    suffix = " (partial period)" if is_partial else ""
    return f"{_human_date_range(start, end)}{suffix}"


def _human_date_range(start: date, end: date) -> str:
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%B')} {start.day}–{end.day}, {end.year}"
    if start.year == end.year:
        return (
            f"{start.strftime('%B')} {start.day}–"
            f"{end.strftime('%B')} {end.day}, {end.year}"
        )
    return (
        f"{start.strftime('%B')} {start.day}, {start.year}–"
        f"{end.strftime('%B')} {end.day}, {end.year}"
    )


def _window(label: str, start: date, end: date, role: str) -> CoachEvidenceWindow:
    return CoachEvidenceWindow(
        label=label,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        role=role,
    )


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, month_zero_based = divmod(month_index, 12)
    month = month_zero_based + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _has_historical_intent(normalized: str) -> bool:
    words = set(normalized.split())
    return bool(
        words.intersection(_HISTORICAL_TERMS)
        or _comparison_mode(normalized) != "none"
        or "deload" in normalized
        or "phase" in normalized
    )


def _can_inherit_context(normalized: str) -> bool:
    return bool(
        normalized.startswith(_FOLLOW_UP_PREFIXES)
        or set(normalized.split()).intersection(
            {"it", "that", "this", "those", "them", "then", "also"}
        )
        or _comparison_mode(normalized) != "none"
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s-]", " ", value.lower())).strip()
