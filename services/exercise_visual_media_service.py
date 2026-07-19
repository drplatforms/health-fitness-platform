"""Provider-neutral Visual Media v2 resolution.

Resolution is intentionally deterministic and finite:
direct local -> accepted shared local visual identity -> approved configured
provider mapping -> no media.  The service does not search providers or infer
visual compatibility from exercise names, family, protocol, or measurements.
"""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import database
from models.exercise_catalog_models import (
    ExerciseVisualMediaItem,
    ExerciseVisualMediaResolution,
)
from services.exercise_catalog_service import (
    get_exercise_catalog_entry_by_id,
    get_exercise_form_media,
    get_exercise_taxonomy,
)
from services.exercise_visual_media_provider_manifest import (
    APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY,
    ASCENDAPI_FREE_V1_ATTRIBUTION,
    ASCENDAPI_FREE_V1_PROVIDER,
    ASCENDAPI_FREE_V1_REVIEW_PROVENANCE,
    ASCENDAPI_FREE_V1_RUNTIME_RIGHTS_NOTE,
    SHARED_LOCAL_VISUAL_IDENTITY_OWNERS,
    ExerciseProviderMediaMapping,
)


@dataclass(frozen=True)
class ExerciseVisualMediaResult:
    media: list[ExerciseVisualMediaItem]
    resolution: ExerciseVisualMediaResolution


class AscendApiFreeV1VisualMediaAdapter:
    """Normalize one reviewed free-hosted V1 mapping without provider search."""

    def resolve(
        self,
        mapping: ExerciseProviderMediaMapping,
    ) -> list[ExerciseVisualMediaItem]:
        if mapping.provider != ASCENDAPI_FREE_V1_PROVIDER:
            raise ValueError("Unsupported visual media provider mapping")

        # The evidence-reviewed free V1 URL is the only remote reference
        # emitted. No provider search, download, cache, mirror, or persistence
        # happens here.
        return [
            ExerciseVisualMediaItem(
                media_key=f"{mapping.provider}:{mapping.provider_exercise_id}",
                media_type="animated_image",
                role="movement_demo",
                url=mapping.animated_media_url,
                alt_text=(
                    f"Animated movement demonstration: {mapping.provider_exercise_name}"
                ),
                caption=None,
                source_type="remote_provider",
                source_catalog_exercise_id=None,
                provider=mapping.provider,
                provider_exercise_id=mapping.provider_exercise_id,
                attribution=ASCENDAPI_FREE_V1_ATTRIBUTION,
                provenance=(
                    f"{ASCENDAPI_FREE_V1_REVIEW_PROVENANCE}; "
                    f"{mapping.review_provenance}; "
                    f"{ASCENDAPI_FREE_V1_RUNTIME_RIGHTS_NOTE}"
                ),
            )
        ]


def get_configured_visual_media_provider() -> AscendApiFreeV1VisualMediaAdapter | None:
    """Return the explicit server-side provider configuration, if available.

    Free hosted ExerciseDB V1 is unauthenticated. Explicit provider selection
    is the availability switch; no API key or fake entitlement gate exists.
    """

    if os.getenv("EXERCISE_VISUAL_MEDIA_PROVIDER", "").strip().lower() != (
        ASCENDAPI_FREE_V1_PROVIDER
    ):
        return None
    return AscendApiFreeV1VisualMediaAdapter()


def _local_media_items(
    assets,
    source_catalog_exercise_id: int,
) -> list[ExerciseVisualMediaItem]:
    return [
        ExerciseVisualMediaItem(
            media_key=f"local:{source_catalog_exercise_id}:{asset.media_key}",
            media_type="static_image",
            role=(
                "start_position" if asset.media_key == "start" else "finish_position"
            ),
            url=asset.asset_path,
            alt_text=asset.alt_text,
            caption=asset.caption,
            source_type="local",
            source_catalog_exercise_id=source_catalog_exercise_id,
            provider=None,
            provider_exercise_id=None,
            attribution=None,
            provenance=(
                f"{asset.source_name}; {asset.source_url}; "
                f"{asset.license_name}; {asset.license_url}"
            ),
        )
        for asset in assets
    ]


def _none_result(
    catalog_exercise_id: int,
    visual_identity_slug: str | None,
) -> ExerciseVisualMediaResult:
    return ExerciseVisualMediaResult(
        media=[],
        resolution=ExerciseVisualMediaResolution(
            requested_catalog_exercise_id=catalog_exercise_id,
            visual_identity_slug=visual_identity_slug,
            resolution_mode="none",
            source_type="none",
            source_catalog_exercise_id=None,
            provider=None,
            provider_exercise_id=None,
        ),
    )


def _shared_local_source_id(visual_identity_slug: str) -> int | None:
    owner_name = SHARED_LOCAL_VISUAL_IDENTITY_OWNERS.get(visual_identity_slug)
    if owner_name is None:
        return None

    database_uri = f"{Path(database.DB_PATH).resolve().as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        direct_local_owners = conn.execute(
            """
            SELECT
                exercise.id AS catalog_exercise_id,
                exercise.name,
                taxonomy.visual_identity_slug
            FROM exercise_catalog_exercises AS exercise
            INNER JOIN exercise_catalog_taxonomy AS taxonomy
                ON taxonomy.exercise_id = exercise.id
            INNER JOIN exercise_catalog_form_media AS media
                ON media.exercise_id = exercise.id
            WHERE taxonomy.visual_identity_slug = ?
            GROUP BY exercise.id, exercise.name, taxonomy.visual_identity_slug
            ORDER BY exercise.id
            """,
            (visual_identity_slug,),
        ).fetchall()

    if len(direct_local_owners) > 1:
        raise ValueError(
            "Multiple direct local-media owners found for shared visual identity "
            f"'{visual_identity_slug}'"
        )
    if not direct_local_owners:
        return None

    source = direct_local_owners[0]
    if (
        source["name"] != owner_name
        or source["visual_identity_slug"] != visual_identity_slug
    ):
        return None
    return source["catalog_exercise_id"]


def resolve_exercise_visual_media(
    catalog_exercise_id: int,
) -> ExerciseVisualMediaResult:
    """Resolve one instruction's media through the approved v2 precedence."""

    exercise = get_exercise_catalog_entry_by_id(catalog_exercise_id)
    if exercise is None:
        raise ValueError("Catalog exercise does not exist")

    taxonomy = get_exercise_taxonomy(catalog_exercise_id)
    visual_identity_slug = None if taxonomy is None else taxonomy.visual_identity_slug

    direct_assets = get_exercise_form_media(catalog_exercise_id)
    if direct_assets:
        return ExerciseVisualMediaResult(
            media=_local_media_items(direct_assets, catalog_exercise_id),
            resolution=ExerciseVisualMediaResolution(
                requested_catalog_exercise_id=catalog_exercise_id,
                visual_identity_slug=visual_identity_slug,
                resolution_mode="direct_local",
                source_type="local",
                source_catalog_exercise_id=catalog_exercise_id,
                provider=None,
                provider_exercise_id=None,
            ),
        )

    if visual_identity_slug is None:
        return _none_result(catalog_exercise_id, visual_identity_slug)

    shared_source_id = _shared_local_source_id(visual_identity_slug)
    if shared_source_id is not None and shared_source_id != catalog_exercise_id:
        shared_assets = get_exercise_form_media(shared_source_id)
        # An approved local-share identity must not fall through to a provider.
        if shared_assets:
            return ExerciseVisualMediaResult(
                media=_local_media_items(shared_assets, shared_source_id),
                resolution=ExerciseVisualMediaResolution(
                    requested_catalog_exercise_id=catalog_exercise_id,
                    visual_identity_slug=visual_identity_slug,
                    resolution_mode="shared_local_visual_identity",
                    source_type="local",
                    source_catalog_exercise_id=shared_source_id,
                    provider=None,
                    provider_exercise_id=None,
                ),
            )
        return _none_result(catalog_exercise_id, visual_identity_slug)

    mapping = APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY.get(
        visual_identity_slug
    )
    if mapping is None:
        return _none_result(catalog_exercise_id, visual_identity_slug)
    provider = get_configured_visual_media_provider()
    if provider is None:
        return _none_result(catalog_exercise_id, visual_identity_slug)

    try:
        provider_media = provider.resolve(mapping)
    except (OSError, RuntimeError, ValueError):
        # A configured provider may still be unavailable.  Instruction text is
        # independent of media and remains available.
        return _none_result(catalog_exercise_id, visual_identity_slug)

    return ExerciseVisualMediaResult(
        media=provider_media,
        resolution=ExerciseVisualMediaResolution(
            requested_catalog_exercise_id=catalog_exercise_id,
            visual_identity_slug=visual_identity_slug,
            resolution_mode="provider",
            source_type="remote_provider",
            source_catalog_exercise_id=None,
            provider=mapping.provider,
            provider_exercise_id=mapping.provider_exercise_id,
        ),
    )
