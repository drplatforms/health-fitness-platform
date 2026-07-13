from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import database
from database import get_connection
from models.food_normalization_models import RawFoodSourceRecord
from services.food_canonical_promotion_service import (
    MACRO_NUTRIENT_FIELD_MAP,
    promote_raw_source_record_to_canonical,
)
from services.food_normalization_service import normalize_food_name

MANIFEST_ACTIONS = {
    "VERIFY_ALREADY_LINKED_NO_OP",
    "CREATE_NET_NEW_CANONICAL_FOOD",
}
REAL_DATABASE_PATH = Path(__file__).resolve().parents[1] / "fitness_ai.db"
ManifestAction = Literal["VERIFY_ALREADY_LINKED_NO_OP", "CREATE_NET_NEW_CANONICAL_FOOD"]
ManifestExecutionStatus = Literal["ALIGNED_NO_OP", "ALIGNED_IDEMPOTENT", "PROMOTED"]


@dataclass(frozen=True)
class ManifestItem:
    sequence: int
    proposed_action: ManifestAction
    source_name: str
    data_type: str
    source_record_id: str
    raw_description: str
    food_category: str | None
    canonical_display_name: str
    normalized_name: str
    aliases: tuple[str, ...]
    calories_per_100g: float | None
    protein_g_per_100g: float | None
    carbs_g_per_100g: float | None
    fat_g_per_100g: float | None


@dataclass(frozen=True)
class ManifestPlanItem:
    item: ManifestItem
    raw: RawFoodSourceRecord
    status: ManifestExecutionStatus
    aligned_snapshot: dict[str, object] | None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_external_database_path(database_path: str | Path) -> Path:
    resolved_path = Path(database_path).resolve()
    if resolved_path == REAL_DATABASE_PATH.resolve():
        raise ValueError(
            "Manifest promotion refuses the repository real fitness_ai.db."
        )
    return resolved_path


def _require_external_database() -> None:
    require_external_database_path(database.DB_PATH)


def _number(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"Manifest item {field_name} must be numeric.")
    return float(value)


def load_manifest(
    manifest_path: str | Path,
    *,
    expected_sha256: str,
    expected_item_count: int | None = None,
) -> tuple[str, list[ManifestItem]]:
    path = Path(manifest_path)
    actual_sha256 = _sha256(path)
    if actual_sha256.casefold() != expected_sha256.casefold():
        raise ValueError("Manifest SHA-256 does not match the expected value.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_items = payload["items"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("Manifest must be JSON containing an items array.") from error
    if not isinstance(raw_items, list):
        raise ValueError("Manifest items must be an array.")
    if expected_item_count is not None and len(raw_items) != expected_item_count:
        raise ValueError(
            f"Manifest contains {len(raw_items)} items, expected {expected_item_count}."
        )

    items: list[ManifestItem] = []
    sequences: set[int] = set()
    identities: set[tuple[str, str, str]] = set()
    names: dict[str, int] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("Manifest items must be objects.")
        action = raw_item.get("proposed_action")
        if action not in MANIFEST_ACTIONS:
            raise ValueError(f"Unexpected manifest action: {action!r}.")
        required_text = (
            "source_name",
            "data_type",
            "source_record_id",
            "raw_description",
            "canonical_display_name",
            "normalized_name",
        )
        if any(
            not isinstance(raw_item.get(key), str) or not raw_item[key].strip()
            for key in required_text
        ):
            raise ValueError("Manifest item has a required blank text field.")
        if not isinstance(raw_item.get("sequence"), int) or raw_item["sequence"] <= 0:
            raise ValueError("Manifest sequence must be a positive integer.")
        aliases = raw_item.get("aliases", [])
        if not isinstance(aliases, list) or any(
            not isinstance(alias, str) for alias in aliases
        ):
            raise ValueError("Manifest aliases must be a string array.")
        canonical_display_name = raw_item["canonical_display_name"].strip()
        normalized_name = normalize_food_name(canonical_display_name)
        normalized_aliases: set[str] = set()
        resolved_aliases: list[str] = []
        for alias in aliases:
            stripped_alias = alias.strip()
            if not stripped_alias:
                continue
            normalized_alias = normalize_food_name(stripped_alias)
            if normalized_alias in normalized_aliases:
                raise ValueError(
                    "Manifest item has duplicate aliases after normalization."
                )
            normalized_aliases.add(normalized_alias)
            if normalized_alias != normalized_name:
                resolved_aliases.append(stripped_alias)

        item = ManifestItem(
            sequence=raw_item["sequence"],
            proposed_action=action,
            source_name=raw_item["source_name"].strip(),
            data_type=raw_item["data_type"].strip(),
            source_record_id=raw_item["source_record_id"].strip(),
            raw_description=raw_item["raw_description"].strip(),
            food_category=(raw_item.get("food_category") or None),
            canonical_display_name=canonical_display_name,
            normalized_name=raw_item["normalized_name"].strip(),
            aliases=tuple(resolved_aliases),
            calories_per_100g=_number(
                raw_item.get("calories_per_100g"), "calories_per_100g"
            ),
            protein_g_per_100g=_number(
                raw_item.get("protein_g_per_100g"), "protein_g_per_100g"
            ),
            carbs_g_per_100g=_number(
                raw_item.get("carbs_g_per_100g"), "carbs_g_per_100g"
            ),
            fat_g_per_100g=_number(raw_item.get("fat_g_per_100g"), "fat_g_per_100g"),
        )
        identity = (item.source_name, item.data_type, item.source_record_id)
        if (
            item.sequence in sequences
            or identity in identities
            or normalized_name in names
        ):
            raise ValueError(
                "Manifest has duplicate sequences, source identities, or names."
            )
        if normalize_food_name(item.normalized_name) != normalized_name:
            raise ValueError(
                "Manifest normalized_name does not match canonical_display_name."
            )
        sequences.add(item.sequence)
        identities.add(identity)
        names[normalized_name] = item.sequence
        items.append(item)
    if sorted(sequences) != list(range(1, len(items) + 1)):
        raise ValueError("Manifest sequences must be contiguous starting at 1.")

    alias_owners: dict[str, int] = {}
    for item in items:
        for alias in item.aliases:
            normalized_alias = normalize_food_name(alias)
            name_owner = names.get(normalized_alias)
            if name_owner is not None and name_owner != item.sequence:
                raise ValueError("Manifest alias equals another item's canonical name.")
            alias_owner = alias_owners.get(normalized_alias)
            if alias_owner is not None and alias_owner != item.sequence:
                raise ValueError("Manifest alias is shared by different items.")
            alias_owners[normalized_alias] = item.sequence
    return actual_sha256, sorted(items, key=lambda item: item.sequence)


def _table_counts() -> dict[str, int]:
    conn = get_connection()
    counts = {
        table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in (
            "canonical_foods",
            "canonical_food_aliases",
            "canonical_food_nutrients",
            "food_source_links",
            "food_entries",
            "raw_food_source_records",
        )
    }
    conn.close()
    return counts


def _raw_for_item(item: ManifestItem) -> RawFoodSourceRecord:
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM raw_food_source_records
        WHERE source_name = ? AND data_type = ? AND source_record_id = ?""",
        (item.source_name, item.data_type, item.source_record_id),
    ).fetchone()
    conn.close()
    if row is None:
        raise ValueError(
            f"Manifest source identity was not found: {item.source_record_id}."
        )
    raw = RawFoodSourceRecord(
        id=int(row["id"]),
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        food_category=row["food_category"],
        data_type=row["data_type"],
        calories_per_100g=row["calories_per_100g"],
        protein_g_per_100g=row["protein_g_per_100g"],
        carbs_g_per_100g=row["carbs_g_per_100g"],
        fat_g_per_100g=row["fat_g_per_100g"],
    )
    if (raw.raw_description, raw.food_category) != (
        item.raw_description,
        item.food_category,
    ):
        raise ValueError(f"Raw source evidence mismatch for {item.source_record_id}.")
    macro_fields = (
        "calories_per_100g",
        "protein_g_per_100g",
        "carbs_g_per_100g",
        "fat_g_per_100g",
    )
    for field_name in macro_fields:
        expected_value = getattr(item, field_name)
        actual_value = getattr(raw, field_name)
        if expected_value is None:
            mismatched = actual_value is not None
        else:
            mismatched = (
                actual_value is None
                or abs(float(actual_value) - expected_value) > 0.000001
            )
        if mismatched:
            raise ValueError(
                f"Raw source evidence mismatch for {item.source_record_id}."
            )
    return raw


def _primary_link(raw_id: int):
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM food_source_links
        WHERE raw_food_source_record_id = ? AND relationship_type = 'primary'""",
        (raw_id,),
    ).fetchone()
    conn.close()
    return row


def _assert_aligned(
    item: ManifestItem,
    raw: RawFoodSourceRecord,
    canonical_id: int,
) -> dict[str, object]:
    conn = get_connection()
    food = conn.execute(
        "SELECT display_name FROM canonical_foods WHERE id = ?", (canonical_id,)
    ).fetchone()
    alias_rows = conn.execute(
        """SELECT alias, normalized_alias FROM canonical_food_aliases
        WHERE canonical_food_id = ? ORDER BY priority, alias""",
        (canonical_id,),
    ).fetchall()
    nutrient_rows = conn.execute(
        """SELECT nutrient_name, amount_per_100g
        FROM canonical_food_nutrients WHERE canonical_food_id = ?""",
        (canonical_id,),
    ).fetchall()
    conn.close()
    if food is None or normalize_food_name(food["display_name"]) != normalize_food_name(
        item.canonical_display_name
    ):
        raise ValueError(f"Canonical name is not aligned for {item.source_record_id}.")
    stored_aliases = {row["normalized_alias"] for row in alias_rows}
    expected_aliases = {
        normalize_food_name(alias)
        for alias in item.aliases
        if normalize_food_name(alias)
        != normalize_food_name(item.canonical_display_name)
    }
    if not expected_aliases.issubset(stored_aliases):
        raise ValueError(
            f"Canonical aliases are not aligned for {item.source_record_id}."
        )
    nutrients = {row["nutrient_name"]: row["amount_per_100g"] for row in nutrient_rows}
    for nutrient_name, _, raw_field in MACRO_NUTRIENT_FIELD_MAP:
        raw_value = getattr(raw, raw_field)
        if raw_value is None:
            mismatched = nutrient_name in nutrients
        else:
            mismatched = (
                nutrient_name not in nutrients
                or abs(nutrients[nutrient_name] - raw_value) > 0.01
            )
        if mismatched:
            raise ValueError(
                f"Canonical macros are not aligned for {item.source_record_id}."
            )
    return {
        "canonical_food_id": canonical_id,
        "aliases": sorted(row["alias"] for row in alias_rows),
        "nutrients": {
            nutrient_name: nutrients[nutrient_name]
            for nutrient_name, _, _ in MACRO_NUTRIENT_FIELD_MAP
            if nutrient_name in nutrients
        },
        "primary_source_link": {
            "raw_food_source_record_id": raw.id,
            "relationship_type": "primary",
        },
    }


def _assert_no_collision(item: ManifestItem) -> None:
    normalized_name = normalize_food_name(item.canonical_display_name)
    candidates = {
        normalized_name,
        *(normalize_food_name(alias) for alias in item.aliases),
    }
    placeholders = ",".join("?" for _ in candidates)
    params = tuple(sorted(candidates))
    conn = get_connection()
    name_collision = conn.execute(
        f"SELECT id FROM canonical_foods WHERE normalized_name IN ({placeholders})",
        params,
    ).fetchone()
    alias_collision = conn.execute(
        f"""SELECT canonical_food_id FROM canonical_food_aliases
        WHERE normalized_alias IN ({placeholders})""",
        params,
    ).fetchone()
    conn.close()
    if name_collision or alias_collision:
        raise ValueError(
            f"Existing canonical name or alias collision for {item.source_record_id}."
        )


def _preflight_manifest(items: list[ManifestItem]) -> list[ManifestPlanItem]:
    plan: list[ManifestPlanItem] = []
    for item in items:
        raw = _raw_for_item(item)
        link = _primary_link(raw.id)
        if item.proposed_action == "VERIFY_ALREADY_LINKED_NO_OP":
            if link is None:
                raise ValueError(
                    f"Expected primary source link is absent for {item.source_record_id}."
                )
            snapshot = _assert_aligned(item, raw, int(link["canonical_food_id"]))
            plan.append(ManifestPlanItem(item, raw, "ALIGNED_NO_OP", snapshot))
        elif link is not None:
            snapshot = _assert_aligned(item, raw, int(link["canonical_food_id"]))
            plan.append(ManifestPlanItem(item, raw, "ALIGNED_IDEMPOTENT", snapshot))
        else:
            _assert_no_collision(item)
            plan.append(ManifestPlanItem(item, raw, "PROMOTED", None))
    return plan


def execute_manifest(
    manifest_path: str | Path,
    *,
    expected_sha256: str,
    expected_item_count: int | None = None,
) -> dict[str, object]:
    _require_external_database()
    manifest_sha256, items = load_manifest(
        manifest_path,
        expected_sha256=expected_sha256,
        expected_item_count=expected_item_count,
    )
    before_counts = _table_counts()
    plan = _preflight_manifest(items)
    results: list[dict[str, object]] = []
    for plan_item in plan:
        item = plan_item.item
        raw = plan_item.raw
        if plan_item.status != "PROMOTED":
            snapshot = plan_item.aligned_snapshot
            if snapshot is None:
                raise ValueError("Validated manifest plan lost its aligned snapshot.")
            results.append(
                {
                    "sequence": item.sequence,
                    "action": item.proposed_action,
                    "status": plan_item.status,
                    "before": snapshot,
                    "after": snapshot,
                }
            )
            continue
        result = promote_raw_source_record_to_canonical(
            raw.id, canonical_name=item.canonical_display_name, aliases=item.aliases
        )
        snapshot = _assert_aligned(item, raw, result.canonical_food.id)
        results.append(
            {
                "sequence": item.sequence,
                "action": item.proposed_action,
                "status": "PROMOTED",
                "before": {
                    "canonical_food_id": None,
                    "aliases": [],
                    "nutrients": {},
                    "primary_source_link": None,
                },
                "after": snapshot,
            }
        )
    after_counts = _table_counts()
    return {
        "manifest_sha256": manifest_sha256,
        "manifest_item_count": len(items),
        "pre_table_counts": before_counts,
        "post_table_counts": after_counts,
        "results": results,
        "summary": {
            status: sum(result["status"] == status for result in results)
            for status in ("ALIGNED_NO_OP", "ALIGNED_IDEMPOTENT", "PROMOTED")
        },
    }


def report_json(report: dict[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, default=asdict)
