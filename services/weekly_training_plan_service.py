from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Any

from database import get_connection
from models.weekly_training_plan_models import (
    WeeklySessionDirective,
    WeeklyTrainingPlan,
    WeeklyTrainingPlanDay,
)
from services.workout_daily_state_service import resolve_workout_daily_state

WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
WORKOUT_SIZE_PREFERENCES = {"quick", "standard", "extended"}

SESSION_TEMPLATES: dict[str, dict[str, Any]] = {
    "full_body_a": {
        "title": "Full Body A",
        "focus": "Balanced full-body strength with a squat emphasis.",
        "slots": ["squat", "horizontal_push", "horizontal_pull", "core", "accessory"],
        "extensions": ["arms", "conditioning_finish"],
    },
    "full_body_b": {
        "title": "Full Body B",
        "focus": "Balanced full-body strength with a hinge emphasis.",
        "slots": ["hinge", "vertical_push", "vertical_pull", "lunge", "core"],
        "extensions": ["accessory", "carry"],
    },
    "full_body_c": {
        "title": "Full Body C",
        "focus": "Balanced full-body strength with varied primary movement patterns.",
        "slots": [
            "lower_primary",
            "push_primary",
            "pull_primary",
            "shoulder_upper_back",
            "conditioning_finish",
        ],
        "extensions": ["core", "arms"],
    },
    "upper_a": {
        "title": "Upper A",
        "focus": "Upper-body strength led by horizontal pressing and pulling.",
        "slots": [
            "horizontal_push",
            "horizontal_pull",
            "vertical_push",
            "vertical_pull",
            "arms",
        ],
        "extensions": ["core", "shoulder_upper_back"],
    },
    "upper_b": {
        "title": "Upper B",
        "focus": "Upper-body strength led by vertical pressing and pulling.",
        "slots": [
            "vertical_push",
            "vertical_pull",
            "horizontal_push",
            "horizontal_pull",
            "core",
        ],
        "extensions": ["arms", "shoulder_upper_back"],
    },
    "upper_c": {
        "title": "Upper C",
        "focus": "Upper-body strength with shoulder, upper-back, and arm support.",
        "slots": [
            "horizontal_push",
            "vertical_pull",
            "shoulder_upper_back",
            "arms",
            "core",
        ],
        "extensions": ["vertical_push", "horizontal_pull"],
    },
    "lower_a": {
        "title": "Lower A",
        "focus": "Lower-body strength led by the squat pattern.",
        "slots": ["squat", "hinge", "lunge", "core", "carry"],
        "extensions": ["accessory", "conditioning_finish"],
    },
    "lower_b": {
        "title": "Lower B",
        "focus": "Lower-body strength led by the hinge pattern.",
        "slots": ["hinge", "squat", "lunge", "core", "conditioning_finish"],
        "extensions": ["carry", "accessory"],
    },
    "lower_c": {
        "title": "Lower C",
        "focus": "Lower-body strength led by unilateral leg work.",
        "slots": ["lunge", "hinge", "squat", "core", "carry"],
        "extensions": ["accessory", "conditioning_finish"],
    },
}

FREQUENCY_SEQUENCES: dict[int, list[str]] = {
    1: ["full_body_a"],
    2: ["full_body_a", "full_body_b"],
    3: ["full_body_a", "full_body_b", "full_body_c"],
    4: ["upper_a", "lower_a", "upper_b", "lower_b"],
    5: ["upper_a", "lower_a", "full_body_c", "upper_b", "lower_b"],
    6: ["upper_a", "lower_a", "upper_b", "lower_b", "upper_c", "lower_c"],
}


class WeeklyTrainingPlanError(Exception):
    pass


class WeeklyTrainingPlanValidationError(WeeklyTrainingPlanError):
    pass


class WeeklyTrainingPlanNotFoundError(WeeklyTrainingPlanError):
    pass


class WeeklyTrainingPlanConflictError(WeeklyTrainingPlanError):
    pass


class WeeklyTrainingPlanProtectedDateError(WeeklyTrainingPlanError):
    pass


def ensure_weekly_training_plan_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_training_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_start_date TEXT NOT NULL,
                week_end_date TEXT NOT NULL,
                target_session_count INTEGER NOT NULL,
                default_workout_size_preference TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, week_start_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_training_plan_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weekly_training_plan_id INTEGER NOT NULL,
                training_date TEXT NOT NULL,
                day_index INTEGER NOT NULL,
                day_type TEXT NOT NULL,
                session_sequence_index INTEGER,
                session_type TEXT,
                session_title TEXT,
                session_focus TEXT,
                session_directive_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(weekly_training_plan_id, training_date),
                UNIQUE(weekly_training_plan_id, day_index),
                FOREIGN KEY (weekly_training_plan_id) REFERENCES weekly_training_plans(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _parse_date(value: date | datetime | str, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise WeeklyTrainingPlanValidationError(
            f"{field_name} must be a valid YYYY-MM-DD date."
        ) from exc


def normalize_week_start_date(value: date | datetime | str) -> date:
    parsed = _parse_date(value, "week_start_date")
    return parsed - timedelta(days=parsed.weekday())


def _normalize_current_date(value: date | datetime | str | None) -> date:
    return date.today() if value is None else _parse_date(value, "current_date")


def normalize_training_weekdays(values: Iterable[int]) -> list[int]:
    raw_values = list(values)
    if any(
        isinstance(value, bool) or not isinstance(value, int) for value in raw_values
    ):
        raise WeeklyTrainingPlanValidationError(
            "training_weekdays must contain weekday indexes from 0 (Monday) through 6 (Sunday)."
        )
    if len(raw_values) != len(set(raw_values)):
        raise WeeklyTrainingPlanValidationError(
            "training_weekdays cannot contain duplicates."
        )
    if any(value < 0 or value > 6 for value in raw_values):
        raise WeeklyTrainingPlanValidationError(
            "training_weekdays must contain weekday indexes from 0 (Monday) through 6 (Sunday)."
        )
    if not 1 <= len(raw_values) <= 6:
        raise WeeklyTrainingPlanValidationError(
            "A weekly plan must contain between 1 and 6 training days."
        )
    return sorted(raw_values)


def normalize_default_workout_size_preference(value: str | None) -> str:
    normalized = str(value or "standard").strip().lower()
    if normalized == "full":
        normalized = "extended"
    if normalized not in WORKOUT_SIZE_PREFERENCES:
        raise WeeklyTrainingPlanValidationError(
            "default_workout_size_preference must be quick, standard, or extended."
        )
    return normalized


def _directive(session_type: str, sequence_index: int) -> WeeklySessionDirective:
    template = SESSION_TEMPLATES[session_type]
    return WeeklySessionDirective(
        session_type=session_type,
        session_title=template["title"],
        session_focus=template["focus"],
        ordered_slot_families=list(template["slots"]),
        optional_extension_slot_families=list(template["extensions"]),
        sequence_index=sequence_index,
    )


def build_week_day_specs(
    week_start_date: date | datetime | str,
    training_weekdays: Iterable[int],
) -> list[dict[str, Any]]:
    week_start = normalize_week_start_date(week_start_date)
    weekdays = normalize_training_weekdays(training_weekdays)
    sequence = FREQUENCY_SEQUENCES[len(weekdays)]
    sequence_by_day = {
        weekday: _directive(sequence[index], index)
        for index, weekday in enumerate(weekdays)
    }
    specs: list[dict[str, Any]] = []
    for day_index in range(7):
        directive = sequence_by_day.get(day_index)
        specs.append(
            {
                "training_date": (week_start + timedelta(days=day_index)).isoformat(),
                "day_index": day_index,
                "day_type": "training" if directive else "rest",
                "session_sequence_index": directive.sequence_index
                if directive
                else None,
                "session_type": directive.session_type if directive else None,
                "session_title": directive.session_title if directive else None,
                "session_focus": directive.session_focus if directive else None,
                "session_directive": directive,
            }
        )
    return specs


def _require_user(cursor: sqlite3.Cursor, user_id: int) -> None:
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        raise WeeklyTrainingPlanNotFoundError("User not found.")


def _insert_day(cursor: sqlite3.Cursor, plan_id: int, spec: dict[str, Any]) -> None:
    directive = spec["session_directive"]
    cursor.execute(
        """
        INSERT INTO weekly_training_plan_days (
            weekly_training_plan_id,
            training_date,
            day_index,
            day_type,
            session_sequence_index,
            session_type,
            session_title,
            session_focus,
            session_directive_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            spec["training_date"],
            spec["day_index"],
            spec["day_type"],
            spec["session_sequence_index"],
            spec["session_type"],
            spec["session_title"],
            spec["session_focus"],
            json.dumps(asdict(directive), sort_keys=True) if directive else None,
        ),
    )


def create_weekly_training_plan(
    user_id: int,
    week_start_date: date | datetime | str,
    training_weekdays: Iterable[int],
    default_workout_size_preference: str = "standard",
    *,
    current_date: date | datetime | str | None = None,
) -> WeeklyTrainingPlan:
    ensure_weekly_training_plan_tables()
    week_start = normalize_week_start_date(week_start_date)
    weekdays = normalize_training_weekdays(training_weekdays)
    size = normalize_default_workout_size_preference(default_workout_size_preference)
    week_end = week_start + timedelta(days=6)
    specs = build_week_day_specs(week_start, weekdays)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _require_user(cursor, user_id)
        cursor.execute(
            "SELECT id FROM weekly_training_plans WHERE user_id = ? AND week_start_date = ?",
            (user_id, week_start.isoformat()),
        )
        if cursor.fetchone() is not None:
            raise WeeklyTrainingPlanConflictError(
                "A weekly training plan already exists for this user and week."
            )
        cursor.execute(
            """
            INSERT INTO weekly_training_plans (
                user_id,
                week_start_date,
                week_end_date,
                target_session_count,
                default_workout_size_preference,
                status
            ) VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (
                user_id,
                week_start.isoformat(),
                week_end.isoformat(),
                len(weekdays),
                size,
            ),
        )
        plan_id = int(cursor.lastrowid)
        for spec in specs:
            _insert_day(cursor, plan_id, spec)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    plan = get_weekly_training_plan(
        user_id,
        week_start,
        current_date=current_date,
    )
    if plan is None:
        raise WeeklyTrainingPlanError(
            "The weekly training plan could not be loaded after creation."
        )
    return plan


def _directive_from_json(raw_value: str | None) -> WeeklySessionDirective | None:
    if not raw_value:
        return None
    payload = json.loads(raw_value)
    return WeeklySessionDirective(
        session_type=str(payload["session_type"]),
        session_title=str(payload["session_title"]),
        session_focus=str(payload["session_focus"]),
        ordered_slot_families=list(payload["ordered_slot_families"]),
        optional_extension_slot_families=list(
            payload.get("optional_extension_slot_families", [])
        ),
        sequence_index=int(payload["sequence_index"]),
    )


def _derived_day_state(
    user_id: int,
    training_date: date,
    day_type: str,
    current_date: date,
) -> tuple[str, bool, str | None]:
    daily_state = resolve_workout_daily_state(user_id, target_date=training_date)
    state = daily_state.state
    if state == "completed_today":
        derived = "completed" if day_type == "training" else "extra_workout"
    elif training_date < current_date:
        derived = "missed" if day_type == "training" else "rest"
    elif state == "active_today":
        derived = "in_progress"
    elif state == "selected_today":
        derived = "selected"
    elif day_type == "rest":
        derived = "rest"
    elif training_date == current_date:
        derived = "today"
    else:
        derived = "planned"

    if training_date < current_date:
        return derived, True, "Past dates cannot be changed."
    if state == "completed_today":
        return derived, True, "Completed workout dates cannot be changed."
    if state == "active_today":
        return derived, True, "In-progress workout dates cannot be changed."
    if state == "selected_today":
        return derived, True, "Selected workout dates cannot be changed."
    return derived, False, None


def _load_plan(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    week_start_date: str | None = None,
    plan_id: int | None = None,
) -> sqlite3.Row | None:
    if plan_id is not None:
        cursor.execute(
            "SELECT * FROM weekly_training_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id),
        )
    else:
        cursor.execute(
            "SELECT * FROM weekly_training_plans WHERE user_id = ? AND week_start_date = ?",
            (user_id, week_start_date),
        )
    return cursor.fetchone()


def _build_plan_from_row(
    plan_row: sqlite3.Row,
    day_rows: list[sqlite3.Row],
    current_date: date,
) -> WeeklyTrainingPlan:
    days: list[WeeklyTrainingPlanDay] = []
    for row in day_rows:
        training_date = _parse_date(row["training_date"], "training_date")
        derived_status, is_protected, protection_reason = _derived_day_state(
            int(plan_row["user_id"]),
            training_date,
            str(row["day_type"]),
            current_date,
        )
        days.append(
            WeeklyTrainingPlanDay(
                id=int(row["id"]),
                weekly_training_plan_id=int(row["weekly_training_plan_id"]),
                training_date=row["training_date"],
                day_index=int(row["day_index"]),
                day_type=row["day_type"],
                session_sequence_index=row["session_sequence_index"],
                session_type=row["session_type"],
                session_title=row["session_title"],
                session_focus=row["session_focus"],
                session_directive=_directive_from_json(row["session_directive_json"]),
                derived_status=derived_status,
                is_protected=is_protected,
                protection_reason=protection_reason,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        )
    status = (
        "completed"
        if current_date > _parse_date(plan_row["week_end_date"], "week_end_date")
        else str(plan_row["status"])
    )
    return WeeklyTrainingPlan(
        id=int(plan_row["id"]),
        user_id=int(plan_row["user_id"]),
        week_start_date=plan_row["week_start_date"],
        week_end_date=plan_row["week_end_date"],
        target_session_count=int(plan_row["target_session_count"]),
        default_workout_size_preference=plan_row["default_workout_size_preference"],
        status=status,
        days=days,
        created_at=plan_row["created_at"],
        updated_at=plan_row["updated_at"],
    )


def get_weekly_training_plan(
    user_id: int,
    week_start_date: date | datetime | str,
    *,
    current_date: date | datetime | str | None = None,
) -> WeeklyTrainingPlan | None:
    ensure_weekly_training_plan_tables()
    week_start = normalize_week_start_date(week_start_date)
    today = _normalize_current_date(current_date)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        plan_row = _load_plan(
            cursor,
            user_id=user_id,
            week_start_date=week_start.isoformat(),
        )
        if plan_row is None:
            return None
        cursor.execute(
            "SELECT * FROM weekly_training_plan_days WHERE weekly_training_plan_id = ? ORDER BY day_index",
            (plan_row["id"],),
        )
        return _build_plan_from_row(plan_row, list(cursor.fetchall()), today)
    finally:
        conn.close()


def get_weekly_training_plan_by_id(
    user_id: int,
    plan_id: int,
    *,
    current_date: date | datetime | str | None = None,
) -> WeeklyTrainingPlan:
    ensure_weekly_training_plan_tables()
    today = _normalize_current_date(current_date)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        plan_row = _load_plan(cursor, user_id=user_id, plan_id=plan_id)
        if plan_row is None:
            raise WeeklyTrainingPlanNotFoundError("Weekly training plan not found.")
        cursor.execute(
            "SELECT * FROM weekly_training_plan_days WHERE weekly_training_plan_id = ? ORDER BY day_index",
            (plan_id,),
        )
        return _build_plan_from_row(plan_row, list(cursor.fetchall()), today)
    finally:
        conn.close()


def update_weekly_training_plan(
    user_id: int,
    plan_id: int,
    training_weekdays: Iterable[int],
    default_workout_size_preference: str,
    *,
    current_date: date | datetime | str | None = None,
) -> WeeklyTrainingPlan:
    ensure_weekly_training_plan_tables()
    weekdays = normalize_training_weekdays(training_weekdays)
    size = normalize_default_workout_size_preference(default_workout_size_preference)
    today = _normalize_current_date(current_date)
    existing = get_weekly_training_plan_by_id(user_id, plan_id, current_date=today)
    if today > _parse_date(existing.week_end_date, "week_end_date"):
        raise WeeklyTrainingPlanProtectedDateError("Past weekly plans are read-only.")
    proposed_specs = build_week_day_specs(existing.week_start_date, weekdays)
    proposed_by_index = {spec["day_index"]: spec for spec in proposed_specs}

    protected_conflicts: list[str] = []
    for day in existing.days:
        if not day.is_protected:
            continue
        proposed = proposed_by_index[day.day_index]
        if day.day_type != proposed["day_type"]:
            protected_conflicts.append(
                f"{WEEKDAY_NAMES[day.day_index]} {day.training_date} is protected"
            )
    if protected_conflicts:
        raise WeeklyTrainingPlanProtectedDateError(
            "The requested schedule would change protected dates: "
            + "; ".join(protected_conflicts)
            + ". No changes were saved."
        )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        plan_row = _load_plan(cursor, user_id=user_id, plan_id=plan_id)
        if plan_row is None:
            raise WeeklyTrainingPlanNotFoundError("Weekly training plan not found.")
        cursor.execute(
            """
            UPDATE weekly_training_plans
            SET target_session_count = ?, default_workout_size_preference = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (len(weekdays), size, plan_id, user_id),
        )
        protected_indexes = {day.day_index for day in existing.days if day.is_protected}
        for spec in proposed_specs:
            if spec["day_index"] in protected_indexes:
                continue
            directive = spec["session_directive"]
            cursor.execute(
                """
                UPDATE weekly_training_plan_days
                SET day_type = ?, session_sequence_index = ?, session_type = ?,
                    session_title = ?, session_focus = ?, session_directive_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE weekly_training_plan_id = ? AND day_index = ?
                """,
                (
                    spec["day_type"],
                    spec["session_sequence_index"],
                    spec["session_type"],
                    spec["session_title"],
                    spec["session_focus"],
                    json.dumps(asdict(directive), sort_keys=True)
                    if directive
                    else None,
                    plan_id,
                    spec["day_index"],
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return get_weekly_training_plan_by_id(user_id, plan_id, current_date=today)


def resolve_weekly_training_context(
    user_id: int,
    target_date: date | datetime | str,
    *,
    current_date: date | datetime | str | None = None,
    is_override: bool = False,
) -> dict[str, Any]:
    target = _parse_date(target_date, "target_date")
    plan = get_weekly_training_plan(
        user_id,
        normalize_week_start_date(target),
        current_date=current_date or target,
    )
    if plan is None:
        return {
            "has_weekly_plan": False,
            "weekly_plan_id": None,
            "weekly_plan_day_id": None,
            "day_type": None,
            "session_type": None,
            "session_title": None,
            "session_focus": None,
            "session_directive": None,
            "default_workout_size_preference": None,
            "derived_status": None,
            "is_override": is_override,
        }
    day = next(item for item in plan.days if item.training_date == target.isoformat())
    return {
        "has_weekly_plan": True,
        "weekly_plan_id": plan.id,
        "weekly_plan_day_id": day.id,
        "day_type": day.day_type,
        "session_type": day.session_type,
        "session_title": day.session_title,
        "session_focus": day.session_focus,
        "session_directive": asdict(day.session_directive)
        if day.session_directive
        else None,
        "default_workout_size_preference": plan.default_workout_size_preference,
        "derived_status": day.derived_status,
        "is_override": is_override,
    }
