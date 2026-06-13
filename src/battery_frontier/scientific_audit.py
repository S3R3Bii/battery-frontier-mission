from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_RANKING_FIELDS = frozenset(
    {
        "pack_specific_energy_Wh_kg",
        "pack_specific_energy_uncertainty",
        "volumetric_energy_density_Wh_L",
        "cycle_life",
        "safety_assessment",
        "manufacturability_assessment",
        "source_lineage",
        "system_boundary",
        "evidence_class",
    }
)


@dataclass(frozen=True)
class RankingGate:
    allowed: bool
    missing_by_candidate: dict[str, list[str]]
    reason: str


def evaluate_ranking_gate(candidates: list[dict[str, Any]]) -> RankingGate:
    """Block ranking unless every candidate has comparable evidence fields."""
    if not candidates:
        return RankingGate(
            allowed=False,
            missing_by_candidate={},
            reason="No candidate assessments are available.",
        )

    missing: dict[str, list[str]] = {}
    for index, candidate in enumerate(candidates):
        candidate_id = str(candidate.get("id", f"candidate-{index + 1}"))
        absent = sorted(
            field
            for field in REQUIRED_RANKING_FIELDS
            if field not in candidate or candidate[field] in (None, "", [])
        )
        if absent:
            missing[candidate_id] = absent

    if missing:
        return RankingGate(
            allowed=False,
            missing_by_candidate=missing,
            reason="Ranking blocked: required comparable evidence or uncertainty is missing.",
        )
    return RankingGate(
        allowed=True,
        missing_by_candidate={},
        reason="All minimum ranking fields are present; objective weights must still be disclosed.",
    )

