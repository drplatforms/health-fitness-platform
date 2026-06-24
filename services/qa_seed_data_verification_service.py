from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import database
from services.runtime_diagnostics_service import build_database_source

DEFAULT_QA_USER_IDS = (101, 102, 103, 104, 105)

QA_USER_SCENARIOS: dict[int, str] = {
    101: "recovery_limited",
    102: "aligned_managed",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}

RANGE_PRESETS: dict[str, tuple[str, str]] = {
    "latest_seeded_week": ("2026-06-08", "2026-06-14"),
    "previous_seeded_week": ("2026-06-01", "2026-06-07"),
    "recent_14_days": ("2026-06-01", "2026-06-14"),
    "recent_28_days": ("2026-05-18", "2026-06-14"),
    "full_expected_seed_window": ("2025-12-17", "2026-06-14"),
}

DOMAIN_NAMES = (
    "recovery",
    "nutrition",
    "workout_sessions",
    "workout_execution_sessions",
    "actual_sets",
    "planned_workouts",
)


class QASeedVerificationError(ValueError):
    """Raised for invalid CLI/service inputs, not query execution failures."""


@dataclass(frozen=True)
class QASeedDomainSummary:
    domain: str
    available: bool
    row_count: int = 0
    min_date: str | None = None
    max_date: str | None = None
    reason: str | None = None
    distinct_logged_days: int | None = None
    completed_count: int | None = None
    planned_exercise_count: int | None = None


@dataclass(frozen=True)
class QASeedUserSummary:
    user_id: int
    scenario: str
    user_exists: bool
    user_name: str | None
    global_bounds: dict[str, QASeedDomainSummary]
    selected_range_counts: dict[str, QASeedDomainSummary]
    data_quality_label: str
    diagnosis_codes: tuple[str, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class QASeedVerificationReport:
    success: bool
    database_source: dict[str, Any]
    selected_start_date: str
    selected_end_date: str
    users: tuple[QASeedUserSummary, ...]
    summary: dict[str, Any]
    warnings: tuple[str, ...] = ()


def resolve_verification_db_path(db_path: str | Path | None = None) -> Path:
    return (
        Path(db_path if db_path is not None else database.DB_PATH)
        .expanduser()
        .resolve()
    )


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise QASeedVerificationError(
            f"{field_name} must be an ISO date in YYYY-MM-DD format."
        ) from exc


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    start = _parse_iso_date(start_date, "start_date")
    end = _parse_iso_date(end_date, "end_date")
    if start > end:
        raise QASeedVerificationError("start_date must be before or equal to end_date.")
    return start.isoformat(), end.isoformat()


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _fetch_table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _fetch_columns(
    connection: sqlite3.Connection,
    table_names: set[str],
) -> dict[str, set[str]]:
    columns: dict[str, set[str]] = {}
    for table_name in table_names:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns[table_name] = {str(row["name"]) for row in rows}
    return columns


def _has_columns(
    table_columns: dict[str, set[str]],
    table_name: str,
    required_columns: set[str],
) -> bool:
    return required_columns.issubset(table_columns.get(table_name, set()))


def _empty_domain(
    domain: str,
    *,
    available: bool,
    reason: str | None,
) -> QASeedDomainSummary:
    return QASeedDomainSummary(domain=domain, available=available, reason=reason)


def _query_one(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...],
) -> sqlite3.Row | None:
    try:
        return connection.execute(sql, parameters).fetchone()
    except sqlite3.Error:
        return None


def _basic_domain_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    domain: str,
    table_name: str,
    date_column: str,
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    count_distinct_days: bool = False,
) -> QASeedDomainSummary:
    if table_name not in table_names:
        return _empty_domain(
            domain, available=False, reason=f"missing_table:{table_name}"
        )
    if not _has_columns(table_columns, table_name, {"user_id", date_column}):
        return _empty_domain(
            domain, available=False, reason=f"missing_columns:{table_name}"
        )

    distinct_sql = (
        f", COUNT(DISTINCT date({date_column})) AS distinct_logged_days"
        if count_distinct_days
        else ", NULL AS distinct_logged_days"
    )
    where = "WHERE user_id = ?"
    parameters: tuple[Any, ...] = (user_id,)
    if start_date is not None and end_date is not None:
        where += f" AND date({date_column}) BETWEEN date(?) AND date(?)"
        parameters = (user_id, start_date, end_date)

    row = _query_one(
        connection,
        f"""
        SELECT
            COUNT(*) AS row_count,
            MIN(date({date_column})) AS min_date,
            MAX(date({date_column})) AS max_date
            {distinct_sql}
        FROM {table_name}
        {where}
        """,
        parameters,
    )
    if row is None:
        return _empty_domain(
            domain, available=False, reason=f"query_failed:{table_name}"
        )

    distinct_days = row["distinct_logged_days"]
    return QASeedDomainSummary(
        domain=domain,
        available=True,
        row_count=int(row["row_count"] or 0),
        min_date=row["min_date"],
        max_date=row["max_date"],
        distinct_logged_days=(
            int(distinct_days) if distinct_days is not None else None
        ),
    )


def _execution_session_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> QASeedDomainSummary:
    table_name = "workout_execution_sessions"
    domain = "workout_execution_sessions"
    if table_name not in table_names:
        return _empty_domain(
            domain, available=False, reason=f"missing_table:{table_name}"
        )
    required = {"user_id", "status", "completed_at", "started_at", "created_at"}
    if not _has_columns(table_columns, table_name, required):
        return _empty_domain(
            domain, available=False, reason=f"missing_columns:{table_name}"
        )

    date_expr = "date(COALESCE(completed_at, started_at, created_at))"
    where = "WHERE user_id = ?"
    parameters: tuple[Any, ...] = (user_id,)
    if start_date is not None and end_date is not None:
        where += f" AND {date_expr} BETWEEN date(?) AND date(?)"
        parameters = (user_id, start_date, end_date)

    row = _query_one(
        connection,
        f"""
        SELECT
            COUNT(*) AS row_count,
            SUM(CASE WHEN lower(status) = 'completed' THEN 1 ELSE 0 END)
                AS completed_count,
            MIN({date_expr}) AS min_date,
            MAX({date_expr}) AS max_date
        FROM workout_execution_sessions
        {where}
        """,
        parameters,
    )
    if row is None:
        return _empty_domain(
            domain, available=False, reason=f"query_failed:{table_name}"
        )

    return QASeedDomainSummary(
        domain=domain,
        available=True,
        row_count=int(row["row_count"] or 0),
        min_date=row["min_date"],
        max_date=row["max_date"],
        completed_count=int(row["completed_count"] or 0),
    )


def _actual_sets_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> QASeedDomainSummary:
    domain = "actual_sets"
    required_tables = {"workout_execution_set_actuals", "workout_execution_sessions"}
    missing_tables = sorted(required_tables.difference(table_names))
    if missing_tables:
        return _empty_domain(
            domain,
            available=False,
            reason="missing_table:" + ",".join(missing_tables),
        )
    if not _has_columns(
        table_columns,
        "workout_execution_set_actuals",
        {"workout_execution_session_id", "created_at"},
    ):
        return _empty_domain(
            domain,
            available=False,
            reason="missing_columns:workout_execution_set_actuals",
        )
    if not _has_columns(
        table_columns,
        "workout_execution_sessions",
        {"id", "user_id", "started_at", "completed_at", "created_at"},
    ):
        return _empty_domain(
            domain,
            available=False,
            reason="missing_columns:workout_execution_sessions",
        )

    has_workout_sessions = "workout_sessions" in table_names and _has_columns(
        table_columns,
        "workout_sessions",
        {"id", "workout_date"},
    )
    has_actual_workout_session_id = "workout_session_id" in table_columns.get(
        "workout_execution_set_actuals",
        set(),
    )
    has_execution_workout_session_id = "workout_session_id" in table_columns.get(
        "workout_execution_sessions",
        set(),
    )

    if has_workout_sessions:
        if has_actual_workout_session_id and has_execution_workout_session_id:
            join_sql = """
            LEFT JOIN workout_sessions
                ON workout_sessions.id = COALESCE(
                    workout_execution_set_actuals.workout_session_id,
                    workout_execution_sessions.workout_session_id
                )
            """
        elif has_actual_workout_session_id:
            join_sql = """
            LEFT JOIN workout_sessions
                ON workout_sessions.id = workout_execution_set_actuals.workout_session_id
            """
        elif has_execution_workout_session_id:
            join_sql = """
            LEFT JOIN workout_sessions
                ON workout_sessions.id = workout_execution_sessions.workout_session_id
            """
        else:
            join_sql = "LEFT JOIN workout_sessions ON 1 = 0"
        date_expr = """
        date(COALESCE(
            workout_sessions.workout_date,
            workout_execution_sessions.completed_at,
            workout_execution_sessions.started_at,
            workout_execution_set_actuals.created_at
        ))
        """
    else:
        join_sql = ""
        date_expr = """
        date(COALESCE(
            workout_execution_sessions.completed_at,
            workout_execution_sessions.started_at,
            workout_execution_set_actuals.created_at
        ))
        """

    where = "WHERE workout_execution_sessions.user_id = ?"
    parameters: tuple[Any, ...] = (user_id,)
    if start_date is not None and end_date is not None:
        where += f" AND {date_expr} BETWEEN date(?) AND date(?)"
        parameters = (user_id, start_date, end_date)

    row = _query_one(
        connection,
        f"""
        SELECT
            COUNT(*) AS row_count,
            MIN({date_expr}) AS min_date,
            MAX({date_expr}) AS max_date
        FROM workout_execution_set_actuals
        JOIN workout_execution_sessions
            ON workout_execution_sessions.id =
                workout_execution_set_actuals.workout_execution_session_id
        {join_sql}
        {where}
        """,
        parameters,
    )
    if row is None:
        return _empty_domain(
            domain,
            available=False,
            reason="query_failed:workout_execution_set_actuals",
        )

    return QASeedDomainSummary(
        domain=domain,
        available=True,
        row_count=int(row["row_count"] or 0),
        min_date=row["min_date"],
        max_date=row["max_date"],
    )


def _planned_workout_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> QASeedDomainSummary:
    domain = "planned_workouts"
    table_name = "workout_plan_instances"
    if table_name not in table_names:
        return _empty_domain(
            domain, available=False, reason=f"missing_table:{table_name}"
        )
    if not _has_columns(
        table_columns,
        table_name,
        {"id", "user_id", "selected_at", "created_at"},
    ):
        return _empty_domain(
            domain, available=False, reason=f"missing_columns:{table_name}"
        )

    has_planned_exercises = "planned_workout_exercises" in table_names and _has_columns(
        table_columns,
        "planned_workout_exercises",
        {"workout_plan_instance_id"},
    )
    join_sql = (
        """
        LEFT JOIN planned_workout_exercises
            ON planned_workout_exercises.workout_plan_instance_id =
                workout_plan_instances.id
        """
        if has_planned_exercises
        else ""
    )
    planned_exercise_sql = (
        "COUNT(planned_workout_exercises.id) AS planned_exercise_count"
        if has_planned_exercises
        and "id" in table_columns.get("planned_workout_exercises", set())
        else "NULL AS planned_exercise_count"
    )
    date_expr = "date(COALESCE(workout_plan_instances.selected_at, workout_plan_instances.created_at))"
    where = "WHERE workout_plan_instances.user_id = ?"
    parameters: tuple[Any, ...] = (user_id,)
    if start_date is not None and end_date is not None:
        where += f" AND {date_expr} BETWEEN date(?) AND date(?)"
        parameters = (user_id, start_date, end_date)

    row = _query_one(
        connection,
        f"""
        SELECT
            COUNT(DISTINCT workout_plan_instances.id) AS row_count,
            MIN({date_expr}) AS min_date,
            MAX({date_expr}) AS max_date,
            {planned_exercise_sql}
        FROM workout_plan_instances
        {join_sql}
        {where}
        """,
        parameters,
    )
    if row is None:
        return _empty_domain(
            domain, available=False, reason=f"query_failed:{table_name}"
        )

    exercise_count = row["planned_exercise_count"]
    return QASeedDomainSummary(
        domain=domain,
        available=True,
        row_count=int(row["row_count"] or 0),
        min_date=row["min_date"],
        max_date=row["max_date"],
        planned_exercise_count=(
            int(exercise_count) if exercise_count is not None else None
        ),
    )


def _domain_summaries(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    user_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, QASeedDomainSummary]:
    return {
        "recovery": _basic_domain_summary(
            connection,
            table_names,
            table_columns,
            domain="recovery",
            table_name="daily_checkins",
            date_column="checkin_date",
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        ),
        "nutrition": _basic_domain_summary(
            connection,
            table_names,
            table_columns,
            domain="nutrition",
            table_name="food_entries",
            date_column="entry_date",
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            count_distinct_days=True,
        ),
        "workout_sessions": _basic_domain_summary(
            connection,
            table_names,
            table_columns,
            domain="workout_sessions",
            table_name="workout_sessions",
            date_column="workout_date",
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        ),
        "workout_execution_sessions": _execution_session_summary(
            connection,
            table_names,
            table_columns,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        ),
        "actual_sets": _actual_sets_summary(
            connection,
            table_names,
            table_columns,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        ),
        "planned_workouts": _planned_workout_summary(
            connection,
            table_names,
            table_columns,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        ),
    }


def get_user_global_bounds(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    user_id: int,
) -> dict[str, QASeedDomainSummary]:
    return _domain_summaries(connection, table_names, table_columns, user_id=user_id)


def get_user_selected_range_counts(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    user_id: int,
    start_date: str,
    end_date: str,
) -> dict[str, QASeedDomainSummary]:
    return _domain_summaries(
        connection,
        table_names,
        table_columns,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )


def _row_count(summary: dict[str, QASeedDomainSummary], domain: str) -> int:
    return summary.get(domain, QASeedDomainSummary(domain, False)).row_count


def _distinct_days(summary: dict[str, QASeedDomainSummary], domain: str) -> int:
    value = summary.get(domain, QASeedDomainSummary(domain, False)).distinct_logged_days
    return int(value or 0)


def _completed_count(summary: dict[str, QASeedDomainSummary], domain: str) -> int:
    value = summary.get(domain, QASeedDomainSummary(domain, False)).completed_count
    return int(value or 0)


def _any_rows(summary: dict[str, QASeedDomainSummary]) -> bool:
    return any(domain.row_count > 0 for domain in summary.values())


def _range_overlaps_any_global_domain(
    global_bounds: dict[str, QASeedDomainSummary],
    start_date: str,
    end_date: str,
) -> bool:
    for summary in global_bounds.values():
        if summary.min_date and summary.max_date:
            if (
                str(summary.max_date) >= start_date
                and str(summary.min_date) <= end_date
            ):
                return True
    return False


def _unavailable_domains(summary: dict[str, QASeedDomainSummary]) -> list[str]:
    return [domain for domain, value in summary.items() if not value.available]


def classify_user_seed_range(
    *,
    user_exists: bool,
    global_bounds: dict[str, QASeedDomainSummary],
    selected_range_counts: dict[str, QASeedDomainSummary],
    start_date: str,
    end_date: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    diagnoses: list[str] = []
    limitations: list[str] = []

    if not user_exists:
        return "insufficient", ("user_missing",), ("QA user was not found.",)

    unavailable = _unavailable_domains(selected_range_counts)
    if unavailable:
        diagnoses.append("domain_unavailable")
        limitations.append("Unavailable domains: " + ", ".join(sorted(unavailable)))

    selected_has_rows = _any_rows(selected_range_counts)
    global_has_rows = _any_rows(global_bounds)
    overlaps = _range_overlaps_any_global_domain(global_bounds, start_date, end_date)

    recovery = _row_count(selected_range_counts, "recovery")
    nutrition_days = _distinct_days(selected_range_counts, "nutrition")
    workout_sessions = _row_count(selected_range_counts, "workout_sessions")
    execution_sessions = _row_count(selected_range_counts, "workout_execution_sessions")
    completed_execution_sessions = _completed_count(
        selected_range_counts,
        "workout_execution_sessions",
    )
    actual_sets = _row_count(selected_range_counts, "actual_sets")

    training_sessions = max(
        workout_sessions,
        execution_sessions,
        completed_execution_sessions,
    )
    major_categories = sum(
        1
        for value in (
            recovery > 0,
            nutrition_days > 0,
            training_sessions > 0 or actual_sets > 0,
        )
        if value
    )

    if not selected_has_rows:
        if global_has_rows and not overlaps:
            diagnoses.append("selected_range_out_of_bounds")
            return (
                "insufficient",
                tuple(dict.fromkeys(diagnoses)),
                tuple(
                    dict.fromkeys(
                        limitations + ["Selected range is outside live seed bounds."]
                    )
                ),
            )
        if global_has_rows:
            diagnoses.append("no_selected_range_data")
            return (
                "insufficient",
                tuple(dict.fromkeys(diagnoses)),
                tuple(
                    dict.fromkeys(
                        limitations + ["No rows were found in the selected range."]
                    )
                ),
            )
        diagnoses.append("no_selected_range_data")
        return (
            "insufficient",
            tuple(dict.fromkeys(diagnoses + ["seed_missing_suspected"])),
            tuple(
                dict.fromkeys(
                    limitations + ["No global seed rows were found for this user."]
                )
            ),
        )

    strong = (
        recovery >= 5
        and nutrition_days >= 5
        and training_sessions >= 3
        and actual_sets > 0
    )
    usable = major_categories >= 2 and (training_sessions > 0 or actual_sets > 0)

    diagnoses.append(
        "seeded_week_populated" if strong else "seeded_week_sparse_but_present"
    )
    if strong:
        diagnoses.extend(["strong_for_weekly_summary", "usable_for_weekly_summary"])
        return (
            "strong",
            tuple(dict.fromkeys(diagnoses)),
            tuple(dict.fromkeys(limitations)),
        )
    if usable:
        diagnoses.append("usable_for_weekly_summary")
        return (
            "usable",
            tuple(dict.fromkeys(diagnoses)),
            tuple(dict.fromkeys(limitations)),
        )

    diagnoses.append("insufficient_for_weekly_summary")
    limitations.append("Selected range has data but lacks enough weekly signal.")
    return "limited", tuple(dict.fromkeys(diagnoses)), tuple(dict.fromkeys(limitations))


def _fetch_user_name(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    user_id: int,
) -> tuple[bool, str | None]:
    if "users" not in table_names:
        return False, None
    if not _has_columns(table_columns, "users", {"id", "name"}):
        return False, None
    row = _query_one(connection, "SELECT id, name FROM users WHERE id = ?", (user_id,))
    if row is None:
        return False, None
    return True, str(row["name"])


def _user_summary(
    connection: sqlite3.Connection,
    table_names: set[str],
    table_columns: dict[str, set[str]],
    *,
    user_id: int,
    start_date: str,
    end_date: str,
) -> QASeedUserSummary:
    user_exists, user_name = _fetch_user_name(
        connection,
        table_names,
        table_columns,
        user_id,
    )
    global_bounds = get_user_global_bounds(
        connection,
        table_names,
        table_columns,
        user_id,
    )
    selected_counts = get_user_selected_range_counts(
        connection,
        table_names,
        table_columns,
        user_id,
        start_date,
        end_date,
    )
    quality, diagnoses, limitations = classify_user_seed_range(
        user_exists=user_exists,
        global_bounds=global_bounds,
        selected_range_counts=selected_counts,
        start_date=start_date,
        end_date=end_date,
    )
    return QASeedUserSummary(
        user_id=user_id,
        scenario=QA_USER_SCENARIOS.get(user_id, "unknown"),
        user_exists=user_exists,
        user_name=user_name,
        global_bounds=global_bounds,
        selected_range_counts=selected_counts,
        data_quality_label=quality,
        diagnosis_codes=diagnoses,
        limitations=limitations,
    )


def _missing_db_report(
    db_path: Path,
    start_date: str,
    end_date: str,
    user_ids: tuple[int, ...],
) -> QASeedVerificationReport:
    users = tuple(
        QASeedUserSummary(
            user_id=user_id,
            scenario=QA_USER_SCENARIOS.get(user_id, "unknown"),
            user_exists=False,
            user_name=None,
            global_bounds={
                domain: _empty_domain(
                    domain, available=False, reason="database_missing"
                )
                for domain in DOMAIN_NAMES
            },
            selected_range_counts={
                domain: _empty_domain(
                    domain, available=False, reason="database_missing"
                )
                for domain in DOMAIN_NAMES
            },
            data_quality_label="insufficient",
            diagnosis_codes=("wrong_db_suspected", "user_missing"),
            limitations=("Database file was not found.",),
        )
        for user_id in user_ids
    )
    database_source = build_database_source(db_path=db_path)
    return QASeedVerificationReport(
        success=False,
        database_source=database_source,
        selected_start_date=start_date,
        selected_end_date=end_date,
        users=users,
        summary={
            "users_checked": len(users),
            "users_present": 0,
            "users_with_any_selected_range_data": 0,
            "users_with_strong_selected_range_data": 0,
            "users_with_usable_selected_range_data": 0,
            "users_with_limited_or_insufficient_selected_range_data": len(users),
            "global_diagnosis": "wrong_db_suspected",
            "usable_for_date_range_debug_v2": False,
            "recommended_default_user_id": None,
            "recommended_low_data_user_id": None,
        },
        warnings=(f"Database file was not found at {db_path}.",),
    )


def _global_summary(users: tuple[QASeedUserSummary, ...]) -> dict[str, Any]:
    users_present = sum(1 for user in users if user.user_exists)
    users_with_selected_data = sum(
        1 for user in users if _any_rows(user.selected_range_counts)
    )
    strong_users = [user for user in users if user.data_quality_label == "strong"]
    usable_users = [
        user for user in users if "usable_for_weekly_summary" in user.diagnosis_codes
    ]
    limited_or_insufficient = sum(
        1 for user in users if user.data_quality_label in {"limited", "insufficient"}
    )

    if users_present == 0:
        global_diagnosis = "wrong_db_suspected"
    elif not any(_any_rows(user.global_bounds) for user in users if user.user_exists):
        global_diagnosis = "seed_missing_suspected"
    elif users_with_selected_data == 0:
        global_diagnosis = "range_out_of_bounds_or_no_selected_range_data"
    elif usable_users:
        global_diagnosis = "usable_for_date_range_debug_v2"
    else:
        global_diagnosis = "selected_range_sparse"

    return {
        "users_checked": len(users),
        "users_present": users_present,
        "users_with_any_selected_range_data": users_with_selected_data,
        "users_with_strong_selected_range_data": len(strong_users),
        "users_with_usable_selected_range_data": len(usable_users),
        "users_with_limited_or_insufficient_selected_range_data": limited_or_insufficient,
        "global_diagnosis": global_diagnosis,
        "usable_for_date_range_debug_v2": bool(usable_users),
        "recommended_default_user_id": (
            usable_users[0].user_id if usable_users else None
        ),
        "recommended_low_data_user_id": next(
            (user.user_id for user in users if user.data_quality_label == "limited"),
            None,
        ),
    }


def verify_qa_seed_data(
    *,
    db_path: str | Path | None = None,
    user_ids: tuple[int, ...] | list[int] | None = None,
    start_date: str = RANGE_PRESETS["latest_seeded_week"][0],
    end_date: str = RANGE_PRESETS["latest_seeded_week"][1],
) -> QASeedVerificationReport:
    selected_start, selected_end = validate_date_range(start_date, end_date)
    resolved_path = resolve_verification_db_path(db_path)
    ids = tuple(user_ids or DEFAULT_QA_USER_IDS)

    if not resolved_path.exists():
        return _missing_db_report(resolved_path, selected_start, selected_end, ids)

    database_source = build_database_source(db_path=resolved_path)
    if not database_source.get("sqlite_connectable"):
        return QASeedVerificationReport(
            success=False,
            database_source=database_source,
            selected_start_date=selected_start,
            selected_end_date=selected_end,
            users=(),
            summary={
                "users_checked": len(ids),
                "users_present": 0,
                "users_with_any_selected_range_data": 0,
                "users_with_strong_selected_range_data": 0,
                "users_with_usable_selected_range_data": 0,
                "users_with_limited_or_insufficient_selected_range_data": 0,
                "global_diagnosis": "wrong_db_suspected",
                "usable_for_date_range_debug_v2": False,
                "recommended_default_user_id": None,
                "recommended_low_data_user_id": None,
            },
            warnings=("Database exists but SQLite could not connect to it.",),
        )

    try:
        with _connect_readonly(resolved_path) as connection:
            table_names = _fetch_table_names(connection)
            table_columns = _fetch_columns(connection, table_names)
            users = tuple(
                _user_summary(
                    connection,
                    table_names,
                    table_columns,
                    user_id=user_id,
                    start_date=selected_start,
                    end_date=selected_end,
                )
                for user_id in ids
            )
    except sqlite3.Error:
        return QASeedVerificationReport(
            success=False,
            database_source=database_source,
            selected_start_date=selected_start,
            selected_end_date=selected_end,
            users=(),
            summary={
                "users_checked": len(ids),
                "users_present": 0,
                "users_with_any_selected_range_data": 0,
                "users_with_strong_selected_range_data": 0,
                "users_with_usable_selected_range_data": 0,
                "users_with_limited_or_insufficient_selected_range_data": 0,
                "global_diagnosis": "query_logic_suspected",
                "usable_for_date_range_debug_v2": False,
                "recommended_default_user_id": None,
                "recommended_low_data_user_id": None,
            },
            warnings=("SQLite query failed while verifying QA seed data.",),
        )

    warnings: list[str] = []
    summary = _global_summary(users)
    if summary["users_present"] == 0:
        warnings.append("QA users 101-105 were not found in this database.")
    if summary["global_diagnosis"] == "seed_missing_suspected":
        warnings.append("QA users exist, but no seed rows were found in known domains.")
    if summary["global_diagnosis"] == "range_out_of_bounds_or_no_selected_range_data":
        warnings.append("Selected range returned no rows for all users.")

    return QASeedVerificationReport(
        success=True,
        database_source=database_source,
        selected_start_date=selected_start,
        selected_end_date=selected_end,
        users=users,
        summary=summary,
        warnings=tuple(warnings),
    )


def _format_domain_summary(summary: QASeedDomainSummary) -> str:
    if not summary.available:
        return f"not_available ({summary.reason})"
    base = f"{summary.row_count} rows"
    if summary.distinct_logged_days is not None:
        base += f", {summary.distinct_logged_days} logged days"
    if summary.completed_count is not None:
        base += f", {summary.completed_count} completed"
    if summary.planned_exercise_count is not None:
        base += f", {summary.planned_exercise_count} planned exercises"
    if summary.min_date and summary.max_date:
        base += f", {summary.min_date} to {summary.max_date}"
    return base


def render_qa_seed_verification_report(report: QASeedVerificationReport) -> str:
    source = report.database_source
    lines: list[str] = [
        "QA Seed Data Verification",
        "Database:",
        f"- path: {source.get('resolved_database_path')}",
        f"- exists: {source.get('database_exists')}",
        f"- connectable: {source.get('sqlite_connectable')}",
        f"- tables: {source.get('available_table_count')}",
        "",
        f"Selected range: {report.selected_start_date} through {report.selected_end_date}",
    ]

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in report.warnings)

    for user in report.users:
        lines.extend(
            [
                "",
                f"User {user.user_id} - {user.scenario}",
                f"- exists: {user.user_exists}",
                f"- name: {user.user_name}",
                "- selected recovery: "
                + _format_domain_summary(user.selected_range_counts["recovery"]),
                "- selected nutrition: "
                + _format_domain_summary(user.selected_range_counts["nutrition"]),
                "- selected workout sessions: "
                + _format_domain_summary(
                    user.selected_range_counts["workout_sessions"]
                ),
                "- selected execution sessions: "
                + _format_domain_summary(
                    user.selected_range_counts["workout_execution_sessions"]
                ),
                "- selected actual sets: "
                + _format_domain_summary(user.selected_range_counts["actual_sets"]),
                "- selected planned workouts: "
                + _format_domain_summary(
                    user.selected_range_counts["planned_workouts"]
                ),
                f"- data quality: {user.data_quality_label}",
                "- diagnosis: " + ", ".join(user.diagnosis_codes),
            ]
        )
        if user.limitations:
            lines.append("- limitations: " + "; ".join(user.limitations))

        lines.extend(
            [
                "- global recovery: "
                + _format_domain_summary(user.global_bounds["recovery"]),
                "- global nutrition: "
                + _format_domain_summary(user.global_bounds["nutrition"]),
                "- global workout sessions: "
                + _format_domain_summary(user.global_bounds["workout_sessions"]),
                "- global actual sets: "
                + _format_domain_summary(user.global_bounds["actual_sets"]),
            ]
        )

    lines.extend(
        [
            "",
            "Summary:",
            f"- users checked: {report.summary.get('users_checked')}",
            f"- users present: {report.summary.get('users_present')}",
            "- users with any selected-range data: "
            + str(report.summary.get("users_with_any_selected_range_data")),
            "- users with strong selected-range data: "
            + str(report.summary.get("users_with_strong_selected_range_data")),
            "- users with usable selected-range data: "
            + str(report.summary.get("users_with_usable_selected_range_data")),
            "- users with limited/insufficient selected-range data: "
            + str(
                report.summary.get(
                    "users_with_limited_or_insufficient_selected_range_data"
                )
            ),
            f"- global diagnosis: {report.summary.get('global_diagnosis')}",
            "- usable for Date-Range Debug v2: "
            + str(report.summary.get("usable_for_date_range_debug_v2")),
            "- recommended default user: "
            + str(report.summary.get("recommended_default_user_id")),
            "- recommended low-data user: "
            + str(report.summary.get("recommended_low_data_user_id")),
        ]
    )
    return "\n".join(lines)


def qa_seed_report_to_dict(report: QASeedVerificationReport) -> dict[str, Any]:
    return asdict(report)
