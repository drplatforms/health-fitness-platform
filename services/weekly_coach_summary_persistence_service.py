from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from database import get_connection
from models.weekly_coach_summary_models import (
    ApprovedWeeklyCoachSummary,
    WeeklyCoachSummaryConfidence,
    WeeklyCoachSummaryJobStatus,
    WeeklyCoachSummarySource,
)

WEEKLY_COACH_SUMMARY_TABLE = "weekly_coach_summary_records"
DEFAULT_SUMMARY_VERSION = "weekly_coach_summary_v1"
DEFAULT_CONTEXT_VERSION = "weekly_coach_fixture_context_v1"

_ALLOWED_SANITIZED_METADATA_FIELDS = frozenset(
    {
        "provider_attempted",
        "fallback_used",
        "fallback_reason",
        "parse_status",
        "validation_status",
        "final_summary_source",
        "validation_errors",
        "generated_by",
    }
)

_FORBIDDEN_PERSISTENCE_FIELDS = frozenset(
    {
        "raw_provider_output",
        "provider_raw_output",
        "rejected_provider_output",
        "raw_model_output",
        "raw_llm_output",
        "full_prompt",
        "prompt_text",
        "raw_prompt",
        "raw_context",
        "raw_database_rows",
        "raw_user_notes",
        "scratchpad",
        "chain_of_thought",
        "validation_bypass",
        "secrets",
        "environment_values",
        "stack_trace",
        "traceback",
        "environment_config",
    }
)

_REQUIRED_SUMMARY_SECTIONS = (
    "headline",
    "weekly_overview",
    "recovery_observation",
    "nutrition_observation",
    "training_observation",
    "primary_pattern",
    "recommended_focus",
    "next_week_guidance",
)


class WeeklyCoachSummaryPersistenceError(ValueError):
    """Raised when Weekly Coach Summary persistence would violate boundaries."""


@dataclass(frozen=True)
class PersistedWeeklyCoachSummaryRecord:
    """Sanitized persisted Weekly Coach Summary record."""

    id: int
    record_id: str
    user_id: int
    week_start: str
    week_end: str
    status: str
    source: str
    confidence: str
    public_safe: bool
    displayable: bool
    stale: bool
    expired: bool
    generated_at: str
    created_at: str
    updated_at: str
    expires_at: str | None
    summary_version: str
    context_version: str
    headline: str
    weekly_overview: str
    recovery_observation: str
    nutrition_observation: str
    training_observation: str
    primary_pattern: str
    recommended_focus: str
    next_week_guidance: str
    reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    sanitized_metadata: dict[str, Any]

    @property
    def approved_summary(self) -> ApprovedWeeklyCoachSummary:
        return ApprovedWeeklyCoachSummary(
            headline=self.headline,
            weekly_overview=self.weekly_overview,
            recovery_observation=self.recovery_observation,
            nutrition_observation=self.nutrition_observation,
            training_observation=self.training_observation,
            primary_pattern=self.primary_pattern,
            recommended_focus=self.recommended_focus,
            next_week_guidance=self.next_week_guidance,
            confidence=self.confidence,
            source=self.source,
            public_safe=self.public_safe,
            displayable=self.displayable,
            reason_codes=self.reason_codes,
            limitations=self.limitations,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "record_id": self.record_id,
            "user_id": self.user_id,
            "week_start": self.week_start,
            "week_end": self.week_end,
            "status": self.status,
            "source": self.source,
            "confidence": self.confidence,
            "public_safe": self.public_safe,
            "displayable": self.displayable,
            "stale": self.stale,
            "expired": self.expired,
            "generated_at": self.generated_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "summary_version": self.summary_version,
            "context_version": self.context_version,
            "headline": self.headline,
            "weekly_overview": self.weekly_overview,
            "recovery_observation": self.recovery_observation,
            "nutrition_observation": self.nutrition_observation,
            "training_observation": self.training_observation,
            "primary_pattern": self.primary_pattern,
            "recommended_focus": self.recommended_focus,
            "next_week_guidance": self.next_week_guidance,
            "reason_codes": self.reason_codes,
            "limitations": self.limitations,
            "sanitized_metadata": self.sanitized_metadata,
        }


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _bool_to_int(value: bool) -> int:
    return 1 if bool(value) else 0


def _date_to_iso(value: date | str, field_name: str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise WeeklyCoachSummaryPersistenceError(
                f"{field_name} must be an ISO date string."
            ) from exc
    raise WeeklyCoachSummaryPersistenceError(
        f"{field_name} must be a date or ISO string."
    )


def _safe_json_tuple(values: tuple[str, ...] | list[str] | None) -> str:
    if values is None:
        return "[]"
    if not isinstance(values, tuple | list):
        raise WeeklyCoachSummaryPersistenceError(
            "Expected a tuple/list of sanitized text."
        )
    cleaned = [" ".join(str(value).strip().split()) for value in values]
    cleaned = [value for value in cleaned if value]
    return json.dumps(cleaned, sort_keys=True)


def _decode_json_tuple(payload: str | None) -> tuple[str, ...]:
    if not payload:
        return ()
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return ()
    if not isinstance(decoded, list):
        return ()
    return tuple(str(value) for value in decoded if str(value).strip())


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).strip().lower() in _FORBIDDEN_PERSISTENCE_FIELDS
            or _contains_forbidden_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list | tuple | set):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise WeeklyCoachSummaryPersistenceError("sanitized_metadata must be a dict.")
    if _contains_forbidden_key(metadata):
        raise WeeklyCoachSummaryPersistenceError(
            "sanitized_metadata contains forbidden raw/internal fields."
        )

    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized_key = str(key).strip()
        lowered = normalized_key.lower()
        if lowered not in _ALLOWED_SANITIZED_METADATA_FIELDS:
            raise WeeklyCoachSummaryPersistenceError(
                f"Unsupported sanitized metadata field: {normalized_key}"
            )
        if isinstance(value, bool | int | float) or value is None:
            sanitized[lowered] = value
        elif isinstance(value, str):
            sanitized[lowered] = " ".join(value.strip().split())
        elif isinstance(value, list | tuple):
            sanitized[lowered] = [" ".join(str(item).strip().split()) for item in value]
        else:
            raise WeeklyCoachSummaryPersistenceError(
                f"Unsupported sanitized metadata value for {normalized_key}."
            )
    return sanitized


def _metadata_json(metadata: dict[str, Any] | None) -> str:
    return json.dumps(_sanitize_metadata(metadata), sort_keys=True)


def _decode_metadata(payload: str | None) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


@contextmanager
def _connection_scope(
    connection: sqlite3.Connection | None,
) -> Iterator[tuple[sqlite3.Connection, bool]]:
    if connection is not None:
        connection.row_factory = sqlite3.Row
        yield connection, False
        return

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        yield conn, True
    finally:
        conn.close()


def ensure_weekly_coach_summary_schema(
    connection: sqlite3.Connection | None = None,
) -> None:
    """Create the Weekly Coach Summary persistence table if needed."""

    with _connection_scope(connection) as (conn, owns_connection):
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {WEEKLY_COACH_SUMMARY_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence TEXT NOT NULL,
                public_safe INTEGER NOT NULL DEFAULT 0,
                displayable INTEGER NOT NULL DEFAULT 0,
                stale INTEGER NOT NULL DEFAULT 0,
                expired INTEGER NOT NULL DEFAULT 0,
                generated_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                summary_version TEXT NOT NULL,
                context_version TEXT NOT NULL,
                headline TEXT NOT NULL,
                weekly_overview TEXT NOT NULL,
                recovery_observation TEXT NOT NULL,
                nutrition_observation TEXT NOT NULL,
                training_observation TEXT NOT NULL,
                primary_pattern TEXT NOT NULL,
                recommended_focus TEXT NOT NULL,
                next_week_guidance TEXT NOT NULL,
                reason_codes_json TEXT NOT NULL DEFAULT '[]',
                limitations_json TEXT NOT NULL DEFAULT '[]',
                sanitized_metadata_json TEXT NOT NULL DEFAULT '{{}}'
            )
            """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_weekly_coach_summary_user_week_latest
            ON {WEEKLY_COACH_SUMMARY_TABLE} (
                user_id,
                week_start,
                week_end,
                summary_version,
                context_version,
                stale,
                expired,
                created_at
            )
            """)
        if owns_connection:
            conn.commit()


def _validate_summary_for_save(summary: ApprovedWeeklyCoachSummary) -> None:
    if not isinstance(summary, ApprovedWeeklyCoachSummary):
        raise WeeklyCoachSummaryPersistenceError(
            "summary must be an ApprovedWeeklyCoachSummary."
        )
    if not summary.public_safe:
        raise WeeklyCoachSummaryPersistenceError(
            "Only public_safe weekly summaries may be persisted."
        )
    if not summary.displayable:
        raise WeeklyCoachSummaryPersistenceError(
            "Only displayable weekly summaries may be persisted in v1."
        )
    for field_name in _REQUIRED_SUMMARY_SECTIONS:
        if not str(getattr(summary, field_name)).strip():
            raise WeeklyCoachSummaryPersistenceError(
                f"{field_name} must not be empty before persistence."
            )
    if _FORBIDDEN_PERSISTENCE_FIELDS & set(summary.approved_field_names()):
        raise WeeklyCoachSummaryPersistenceError(
            "Approved summary exposes forbidden persistence fields."
        )


def _row_to_record(row: sqlite3.Row | None) -> PersistedWeeklyCoachSummaryRecord | None:
    if row is None:
        return None
    return PersistedWeeklyCoachSummaryRecord(
        id=int(row["id"]),
        record_id=str(row["record_id"]),
        user_id=int(row["user_id"]),
        week_start=str(row["week_start"]),
        week_end=str(row["week_end"]),
        status=str(row["status"]),
        source=str(row["source"]),
        confidence=str(row["confidence"]),
        public_safe=bool(row["public_safe"]),
        displayable=bool(row["displayable"]),
        stale=bool(row["stale"]),
        expired=bool(row["expired"]),
        generated_at=str(row["generated_at"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        expires_at=row["expires_at"],
        summary_version=str(row["summary_version"]),
        context_version=str(row["context_version"]),
        headline=str(row["headline"]),
        weekly_overview=str(row["weekly_overview"]),
        recovery_observation=str(row["recovery_observation"]),
        nutrition_observation=str(row["nutrition_observation"]),
        training_observation=str(row["training_observation"]),
        primary_pattern=str(row["primary_pattern"]),
        recommended_focus=str(row["recommended_focus"]),
        next_week_guidance=str(row["next_week_guidance"]),
        reason_codes=_decode_json_tuple(row["reason_codes_json"]),
        limitations=_decode_json_tuple(row["limitations_json"]),
        sanitized_metadata=_decode_metadata(row["sanitized_metadata_json"]),
    )


def save_approved_weekly_summary(
    *,
    summary: ApprovedWeeklyCoachSummary,
    user_id: int,
    week_start: date | str,
    week_end: date | str,
    connection: sqlite3.Connection | None = None,
    sanitized_metadata: dict[str, Any] | None = None,
    summary_version: str = DEFAULT_SUMMARY_VERSION,
    context_version: str = DEFAULT_CONTEXT_VERSION,
    expires_at: str | None = None,
) -> PersistedWeeklyCoachSummaryRecord:
    """Persist one approved Weekly Coach Summary and mark older matching records stale.

    Duplicate policy for v1: insert a new record and mark previous matching
    user/week/version records stale. Latest retrieval returns the newest non-stale,
    non-expired, public-safe, displayable approved summary.
    """

    _validate_summary_for_save(summary)
    user_id = int(user_id)
    if user_id <= 0:
        raise WeeklyCoachSummaryPersistenceError("user_id must be positive.")
    start = _date_to_iso(week_start, "week_start")
    end = _date_to_iso(week_end, "week_end")
    if start > end:
        raise WeeklyCoachSummaryPersistenceError(
            "week_start must be on or before week_end."
        )
    metadata_payload = _metadata_json(sanitized_metadata)
    now = _now_iso()
    record_id = f"wcs-{uuid.uuid4().hex}"

    try:
        WeeklyCoachSummaryConfidence(summary.confidence.value)
        WeeklyCoachSummarySource(summary.source.value)
    except (AttributeError, ValueError) as exc:
        raise WeeklyCoachSummaryPersistenceError(
            "summary confidence/source must use approved weekly summary vocabulary."
        ) from exc

    with _connection_scope(connection) as (conn, owns_connection):
        ensure_weekly_coach_summary_schema(conn)
        conn.execute(
            f"""
            UPDATE {WEEKLY_COACH_SUMMARY_TABLE}
            SET stale = 1, updated_at = ?
            WHERE user_id = ?
              AND week_start = ?
              AND week_end = ?
              AND summary_version = ?
              AND context_version = ?
              AND stale = 0
            """,
            (now, user_id, start, end, summary_version, context_version),
        )
        conn.execute(
            f"""
            INSERT INTO {WEEKLY_COACH_SUMMARY_TABLE} (
                record_id,
                user_id,
                week_start,
                week_end,
                status,
                source,
                confidence,
                public_safe,
                displayable,
                stale,
                expired,
                generated_at,
                created_at,
                updated_at,
                expires_at,
                summary_version,
                context_version,
                headline,
                weekly_overview,
                recovery_observation,
                nutrition_observation,
                training_observation,
                primary_pattern,
                recommended_focus,
                next_week_guidance,
                reason_codes_json,
                limitations_json,
                sanitized_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                user_id,
                start,
                end,
                WeeklyCoachSummaryJobStatus.APPROVED.value,
                summary.source.value,
                summary.confidence.value,
                _bool_to_int(summary.public_safe),
                _bool_to_int(summary.displayable),
                now,
                now,
                now,
                expires_at,
                summary_version,
                context_version,
                summary.headline,
                summary.weekly_overview,
                summary.recovery_observation,
                summary.nutrition_observation,
                summary.training_observation,
                summary.primary_pattern,
                summary.recommended_focus,
                summary.next_week_guidance,
                _safe_json_tuple(summary.reason_codes),
                _safe_json_tuple(summary.limitations),
                metadata_payload,
            ),
        )
        if owns_connection:
            conn.commit()
        record = get_weekly_summary_by_id(record_id, connection=conn)
        if record is None:
            raise WeeklyCoachSummaryPersistenceError(
                "Saved weekly summary could not be reloaded."
            )
        return record


def get_weekly_summary_by_id(
    record_id: str | int,
    *,
    connection: sqlite3.Connection | None = None,
) -> PersistedWeeklyCoachSummaryRecord | None:
    """Load one persisted Weekly Coach Summary by public record id or integer id."""

    with _connection_scope(connection) as (conn, _owns_connection):
        ensure_weekly_coach_summary_schema(conn)
        if isinstance(record_id, int):
            row = conn.execute(
                f"SELECT * FROM {WEEKLY_COACH_SUMMARY_TABLE} WHERE id = ?",
                (record_id,),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT * FROM {WEEKLY_COACH_SUMMARY_TABLE} WHERE record_id = ?",
                (str(record_id),),
            ).fetchone()
        return _row_to_record(row)


def get_latest_approved_weekly_summary(
    *,
    user_id: int,
    week_start: date | str,
    week_end: date | str,
    connection: sqlite3.Connection | None = None,
    summary_version: str = DEFAULT_SUMMARY_VERSION,
    context_version: str = DEFAULT_CONTEXT_VERSION,
) -> PersistedWeeklyCoachSummaryRecord | None:
    """Return the latest eligible approved/public-safe weekly summary."""

    start = _date_to_iso(week_start, "week_start")
    end = _date_to_iso(week_end, "week_end")
    with _connection_scope(connection) as (conn, _owns_connection):
        ensure_weekly_coach_summary_schema(conn)
        row = conn.execute(
            f"""
            SELECT * FROM {WEEKLY_COACH_SUMMARY_TABLE}
            WHERE user_id = ?
              AND week_start = ?
              AND week_end = ?
              AND summary_version = ?
              AND context_version = ?
              AND status = ?
              AND public_safe = 1
              AND displayable = 1
              AND stale = 0
              AND expired = 0
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (
                int(user_id),
                start,
                end,
                summary_version,
                context_version,
                WeeklyCoachSummaryJobStatus.APPROVED.value,
            ),
        ).fetchone()
        return _row_to_record(row)


def list_weekly_summaries_for_user(
    *,
    user_id: int,
    connection: sqlite3.Connection | None = None,
    limit: int = 20,
) -> tuple[PersistedWeeklyCoachSummaryRecord, ...]:
    """Return a bounded list of sanitized persisted weekly summaries for Developer Mode."""

    bounded_limit = max(1, min(int(limit), 50))
    with _connection_scope(connection) as (conn, _owns_connection):
        ensure_weekly_coach_summary_schema(conn)
        rows = conn.execute(
            f"""
            SELECT * FROM {WEEKLY_COACH_SUMMARY_TABLE}
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (int(user_id), bounded_limit),
        ).fetchall()
        return tuple(record for row in rows if (record := _row_to_record(row)))


def mark_weekly_summary_stale(
    record_id: str | int,
    *,
    connection: sqlite3.Connection | None = None,
) -> bool:
    """Mark one persisted Weekly Coach Summary record stale."""

    now = _now_iso()
    with _connection_scope(connection) as (conn, owns_connection):
        ensure_weekly_coach_summary_schema(conn)
        if isinstance(record_id, int):
            cursor = conn.execute(
                f"UPDATE {WEEKLY_COACH_SUMMARY_TABLE} SET stale = 1, updated_at = ? WHERE id = ?",
                (now, record_id),
            )
        else:
            cursor = conn.execute(
                f"UPDATE {WEEKLY_COACH_SUMMARY_TABLE} SET stale = 1, updated_at = ? WHERE record_id = ?",
                (now, str(record_id)),
            )
        if owns_connection:
            conn.commit()
        return cursor.rowcount > 0
