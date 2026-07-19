"""Reviewed, repository-owned provider media mappings for Visualization v2.

The provider is a media source only.  Exercise identity and physical visual
identity remain owned by the catalog and taxonomy projections.  This module is
deliberately an explicit allowlist derived from the accepted reassessment; it
must never be replaced with a provider search or name-matching fallback.
"""

from dataclasses import dataclass
from types import MappingProxyType

ASCENDAPI_FREE_V1_PROVIDER = "ascendapi_free_v1"
ASCENDAPI_FREE_V1_SOURCE_ENDPOINT = "https://oss.exercisedb.dev/api/v1/exercises"
ASCENDAPI_FREE_V1_MEDIA_BASE_URL = "https://static.exercisedb.dev/media/"
ASCENDAPI_FREE_V1_ATTRIBUTION = (
    "Animated demonstration provided by ExerciseDB / AscendAPI Free V1."
)
ASCENDAPI_FREE_V1_RUNTIME_RIGHTS_NOTE = (
    "Free hosted ExerciseDB V1 media authorized only for the current "
    "non-commercial prototype phase; provider rights must be revisited before "
    "any monetized or SaaS launch; no local caching, vendoring, mirroring, or "
    "redistribution."
)
ASCENDAPI_FREE_V1_REVIEW_PROVENANCE = (
    "docs/project_memory/spikes/ascendapi_structured_coverage_reassessment_v1.md"
)


@dataclass(frozen=True)
class ExerciseProviderMediaMapping:
    visual_identity_slug: str
    provider: str
    provider_exercise_id: str
    provider_exercise_name: str
    animated_media_url: str
    review_provenance: str


# These owner identities are the only approved internal local-media reuse
# groups.  Runtime checks taxonomy on both the requested and source exercise;
# source names here identify the existing direct local owners, not name fallback.
SHARED_LOCAL_VISUAL_IDENTITY_OWNERS = MappingProxyType(
    {
        "visual_push_up": "Push-Up",
        "visual_goblet_squat": "Goblet Squat",
        "visual_treadmill_walk": "Treadmill Walk",
    }
)


APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS = (
    ExerciseProviderMediaMapping(
        "visual_back_squat",
        "ascendapi_free_v1",
        "DhMl549",
        "barbell full squat (back pov)",
        "https://static.exercisedb.dev/media/DhMl549.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_band_pallof_press",
        "ascendapi_free_v1",
        "9pa4H5m",
        "band horizontal pallof press",
        "https://static.exercisedb.dev/media/9pa4H5m.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_band_pull_through",
        "ascendapi_free_v1",
        "VtTbiP3",
        "band pull through",
        "https://static.exercisedb.dev/media/VtTbiP3.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_band_shoulder_press",
        "ascendapi_free_v1",
        "peAeMR3",
        "band shoulder press",
        "https://static.exercisedb.dev/media/peAeMR3.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_band_squat",
        "ascendapi_free_v1",
        "TUZLh71",
        "band squat",
        "https://static.exercisedb.dev/media/TUZLh71.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_barbell_calf_raise",
        "ascendapi_free_v1",
        "8ozhUIZ",
        "barbell standing calf raise",
        "https://static.exercisedb.dev/media/8ozhUIZ.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_barbell_reverse_lunge",
        "ascendapi_free_v1",
        "VaP75jl",
        "barbell rear lunge",
        "https://static.exercisedb.dev/media/VaP75jl.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_bear_crawl",
        "ascendapi_free_v1",
        "0Yz8WdV",
        "bear crawl",
        "https://static.exercisedb.dev/media/0Yz8WdV.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_chest_fly",
        "ascendapi_free_v1",
        "Pr9Rhf4",
        "cable standing fly",
        "https://static.exercisedb.dev/media/Pr9Rhf4.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_external_rotation",
        "ascendapi_free_v1",
        "FWdVhcW",
        "cable standing shoulder external rotation",
        "https://static.exercisedb.dev/media/FWdVhcW.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_lat_pulldown",
        "ascendapi_free_v1",
        "qdRxqCj",
        "cable pulldown (pro lat bar)",
        "https://static.exercisedb.dev/media/qdRxqCj.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_lateral_raise",
        "ascendapi_free_v1",
        "goJ6ezq",
        "cable lateral raise",
        "https://static.exercisedb.dev/media/goJ6ezq.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_pull_through",
        "ascendapi_free_v1",
        "OM46QHm",
        "cable pull through (with rope)",
        "https://static.exercisedb.dev/media/OM46QHm.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_cable_upright_row",
        "ascendapi_free_v1",
        "cALKspW",
        "cable upright row",
        "https://static.exercisedb.dev/media/cALKspW.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_chest_supported_dumbbell_row",
        "ascendapi_free_v1",
        "7vG5o25",
        "dumbbell incline row",
        "https://static.exercisedb.dev/media/7vG5o25.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_chest_supported_rear_delt_fly",
        "ascendapi_free_v1",
        "vYk8lqw",
        "dumbbell incline rear lateral raise",
        "https://static.exercisedb.dev/media/vYk8lqw.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_close_grip_push_up",
        "ascendapi_free_v1",
        "x6KpKpq",
        "close-grip push-up",
        "https://static.exercisedb.dev/media/x6KpKpq.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_calf_raise",
        "ascendapi_free_v1",
        "dPmaUaU",
        "dumbbell standing calf raise",
        "https://static.exercisedb.dev/media/dPmaUaU.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_cross_body_hammer_curl",
        "ascendapi_free_v1",
        "Qyk5J3p",
        "dumbbell cross body hammer curl",
        "https://static.exercisedb.dev/media/Qyk5J3p.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_hammer_curl",
        "ascendapi_free_v1",
        "slDvUAU",
        "dumbbell hammer curl",
        "https://static.exercisedb.dev/media/slDvUAU.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_pullover",
        "ascendapi_free_v1",
        "9XjtHvS",
        "dumbbell pullover",
        "https://static.exercisedb.dev/media/9XjtHvS.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_rdl",
        "ascendapi_free_v1",
        "rR0LJzx",
        "dumbbell romanian deadlift",
        "https://static.exercisedb.dev/media/rR0LJzx.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_rear_delt_fly",
        "ascendapi_free_v1",
        "8DiFDVA",
        "dumbbell rear fly",
        "https://static.exercisedb.dev/media/8DiFDVA.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_reverse_curl",
        "ascendapi_free_v1",
        "0IgNjSM",
        "dumbbell standing reverse curl",
        "https://static.exercisedb.dev/media/0IgNjSM.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_shoulder_press",
        "ascendapi_free_v1",
        "A6wtbuL",
        "dumbbell standing overhead press",
        "https://static.exercisedb.dev/media/A6wtbuL.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_single_leg_rdl",
        "ascendapi_free_v1",
        "gKozT8X",
        "dumbbell single leg deadlift",
        "https://static.exercisedb.dev/media/gKozT8X.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_dumbbell_skull_crusher",
        "ascendapi_free_v1",
        "mpKZGWz",
        "dumbbell lying triceps extension",
        "https://static.exercisedb.dev/media/mpKZGWz.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_ez_bar_jm_press",
        "ascendapi_free_v1",
        "hnOYgH3",
        "ez barbell jm bench press",
        "https://static.exercisedb.dev/media/hnOYgH3.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_ez_bar_overhead_triceps_extension",
        "ascendapi_free_v1",
        "iaapw0g",
        "ez barbell seated triceps extension",
        "https://static.exercisedb.dev/media/iaapw0g.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_ez_bar_reverse_curl",
        "ascendapi_free_v1",
        "Y5X65IB",
        "ez barbell reverse grip curl",
        "https://static.exercisedb.dev/media/Y5X65IB.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_hanging_knee_raise",
        "ascendapi_free_v1",
        "VEcJRo2",
        "hanging leg hip raise",
        "https://static.exercisedb.dev/media/VEcJRo2.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_hanging_oblique_knee_raise",
        "ascendapi_free_v1",
        "BaE7O6U",
        "hanging oblique knee raise",
        "https://static.exercisedb.dev/media/BaE7O6U.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_heel_tap",
        "ascendapi_free_v1",
        "qaZVsGk",
        "alternate heel touchers",
        "https://static.exercisedb.dev/media/qaZVsGk.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_lat_pulldown",
        "ascendapi_free_v1",
        "RVwzP10",
        "cable pulldown",
        "https://static.exercisedb.dev/media/RVwzP10.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_machine_row",
        "ascendapi_free_v1",
        "7I6LNUG",
        "lever seated row",
        "https://static.exercisedb.dev/media/7I6LNUG.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_neutral_grip_pull_up",
        "ascendapi_free_v1",
        "0V2YQjW",
        "pull up (neutral grip)",
        "https://static.exercisedb.dev/media/0V2YQjW.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_pendlay_row",
        "ascendapi_free_v1",
        "r0z6xzQ",
        "barbell pendlay row",
        "https://static.exercisedb.dev/media/r0z6xzQ.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_plank_shoulder_tap",
        "ascendapi_free_v1",
        "yRpV5TC",
        "shoulder tap",
        "https://static.exercisedb.dev/media/yRpV5TC.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_plate_front_raise",
        "ascendapi_free_v1",
        "e4aFmFY",
        "weighted front raise",
        "https://static.exercisedb.dev/media/e4aFmFY.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_rope_hammer_curl",
        "ascendapi_free_v1",
        "HPlPoQA",
        "cable hammer curl (with rope)",
        "https://static.exercisedb.dev/media/HPlPoQA.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_scapular_push_up",
        "ascendapi_free_v1",
        "jV65tKx",
        "scapula push-up",
        "https://static.exercisedb.dev/media/jV65tKx.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_single_arm_cable_row",
        "ascendapi_free_v1",
        "EIsE3u8",
        "cable one arm bent over row",
        "https://static.exercisedb.dev/media/EIsE3u8.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_stationary_bike",
        "ascendapi_free_v1",
        "H1PESYI",
        "stationary bike run",
        "https://static.exercisedb.dev/media/H1PESYI.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_treadmill_incline_walk",
        "ascendapi_free_v1",
        "rjiM4L3",
        "walking on incline treadmill",
        "https://static.exercisedb.dev/media/rjiM4L3.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_waiter_carry",
        "ascendapi_free_v1",
        "mWBtgmb",
        "dumbbell single arm overhead carry",
        "https://static.exercisedb.dev/media/mWBtgmb.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
    ExerciseProviderMediaMapping(
        "visual_wall_push_up",
        "ascendapi_free_v1",
        "LEH9jxP",
        "push-up (wall)",
        "https://static.exercisedb.dev/media/LEH9jxP.gif",
        "ascendapi_structured_coverage_reassessment_v1",
    ),
)

APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY = MappingProxyType(
    {
        mapping.visual_identity_slug: mapping
        for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    }
)

if (
    len(APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS) != 46
    or len(APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY) != 46
    or any(
        mapping.provider != ASCENDAPI_FREE_V1_PROVIDER
        or mapping.animated_media_url
        != (f"{ASCENDAPI_FREE_V1_MEDIA_BASE_URL}{mapping.provider_exercise_id}.gif")
        or not mapping.review_provenance
        for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    )
):
    raise RuntimeError("Approved AscendAPI Free V1 visual-media manifest is invalid")
