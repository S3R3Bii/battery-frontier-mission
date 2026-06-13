from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.data.connectors import dry_run_source
from battery_frontier.provenance import sha256_file
from battery_frontier.registry import Registries, load_registries
from battery_frontier.schemas import MaterialCandidate
from battery_frontier.simulations.campaign import build_long_haul_feasibility_studies

DEFAULT_MATERIALS_DIR = PROJECT_ROOT / "reports" / "materials"
MATERIALS_PROJECT_QUERY = "Li O"
MATERIALS_PROJECT_ROWS = 5


def _mission_requirements() -> list[dict[str, Any]]:
    return [
        {
            "profile_id": row["profile_id"],
            "name": row["name"],
            "distance_km": row["distance_km"],
            "required_pack_specific_energy_Wh_kg": row[
                "required_pack_specific_energy_Wh_kg"
            ],
            "feasibility_status": row["feasibility_status"],
            "claim_boundary": row["claim_boundary"],
        }
        for row in build_long_haul_feasibility_studies()
    ]


def _energy_status(candidate: MaterialCandidate) -> str:
    has_capacity = candidate.theoretical_specific_capacity_mAh_g is not None
    has_voltage = candidate.nominal_voltage_v is not None
    if has_capacity and has_voltage:
        return "estimated_assumption_only"
    if not has_capacity and not has_voltage:
        return "blocked_missing_capacity_and_voltage"
    if not has_capacity:
        return "blocked_missing_capacity"
    return "blocked_missing_voltage"


def _screen_material(candidate: MaterialCandidate) -> dict[str, Any]:
    status = _energy_status(candidate)
    active_Wh_kg = None
    theoretical_pack_Wh_kg = None
    engineered_pack_Wh_kg = None
    engineered_pack_range = None
    if status == "estimated_assumption_only":
        assert candidate.theoretical_specific_capacity_mAh_g is not None
        assert candidate.nominal_voltage_v is not None
        active_Wh_kg = (
            candidate.theoretical_specific_capacity_mAh_g * candidate.nominal_voltage_v
        )
        theoretical_pack_Wh_kg = active_Wh_kg * candidate.pack_overhead_factor
        engineered_pack_Wh_kg = (
            active_Wh_kg
            * candidate.cell_derating_factor
            * candidate.pack_overhead_factor
        )
        engineered_pack_range = {
            "lower_Wh_kg": round(engineered_pack_Wh_kg * 0.75, 3),
            "nominal_Wh_kg": round(engineered_pack_Wh_kg, 3),
            "upper_Wh_kg": round(
                min(theoretical_pack_Wh_kg, engineered_pack_Wh_kg * 1.25),
                3,
            ),
            "range_basis": (
                "Assumption sensitivity bracket only; not statistical uncertainty "
                "and not validated performance."
            ),
        }

    material_hypothesis = candidate.evidence_level.value in {
        "literature_projection",
        "simulation_estimate",
        "theoretical_limit",
        "speculative_hypothesis",
    }
    hemp_guardrail = ""
    if "hemp" in candidate.id or "bast" in candidate.display_name.lower():
        hemp_guardrail = (
            "Exploratory carbon architecture; included for hypothesis tracking only. "
            "No validated aviation battery performance is claimed."
        )

    return {
        "artifact_type": "material_candidate_card",
        "material_id": candidate.material_id,
        "display_name": candidate.display_name,
        "chemistry_family_id": candidate.chemistry_family_id,
        "chemistry_family": candidate.chemistry_family,
        "role": candidate.role,
        "evidence_level": candidate.evidence_level.value,
        "source_type": candidate.source_type,
        "system_boundary": candidate.system_boundary,
        "theoretical_basis": candidate.theoretical_basis,
        "measured_basis": candidate.measured_basis,
        "aviation_relevance": candidate.aviation_relevance,
        "key_limitations": candidate.key_limitations,
        "toxicity_safety_flags": candidate.toxicity_safety_flags,
        "abundance_supply_flags": candidate.abundance_supply_flags,
        "manufacturability_flags": candidate.manufacturability_flags,
        "theoretical_specific_capacity_mAh_g": (
            candidate.theoretical_specific_capacity_mAh_g
        ),
        "nominal_voltage_v": candidate.nominal_voltage_v,
        "nominal_voltage_note": candidate.nominal_voltage_note,
        "cell_derating_factor": candidate.cell_derating_factor,
        "pack_overhead_factor": candidate.pack_overhead_factor,
        "energy_estimate_status": status,
        "theoretical_active_material_Wh_kg": (
            round(active_Wh_kg, 3) if active_Wh_kg is not None else None
        ),
        "theoretical_only_pack_Wh_kg": (
            round(theoretical_pack_Wh_kg, 3)
            if theoretical_pack_Wh_kg is not None
            else None
        ),
        "engineering_bounded_pack_Wh_kg": (
            round(engineered_pack_Wh_kg, 3)
            if engineered_pack_Wh_kg is not None
            else None
        ),
        "implied_pack_Wh_kg_range": engineered_pack_range,
        "material_hypothesis": material_hypothesis,
        "performance_evidence": False,
        "audited_measurement": False,
        "ranking_evidence": False,
        "may_appear_in_audited_lane": candidate.may_appear_in_audited_lane,
        "citation_ids": candidate.citation_ids,
        "source_urls": [str(url) for url in candidate.source_urls],
        "hemp_bast_fiber_guardrail": hemp_guardrail,
        "claim_boundary": (
            "Material screening diagnostic only. This row is not DFT proof, "
            "experimental validation, pack proof, or a candidate ranking."
        ),
    }


def _frontier_gap_rows(
    cards: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card in cards:
        pack_energy = card["engineering_bounded_pack_Wh_kg"]
        for requirement in requirements:
            required = float(requirement["required_pack_specific_energy_Wh_kg"])
            if pack_energy is None:
                gap = None
                sufficiency = None
                status = "not_energy_estimated"
            else:
                gap = required - float(pack_energy)
                sufficiency = float(pack_energy) / required
                status = (
                    "diagnostic_meets_or_exceeds_requirement"
                    if gap <= 0
                    else "gap_remaining"
                )
            rows.append(
                {
                    "artifact_type": "material_frontier_gap",
                    "material_id": card["material_id"],
                    "display_name": card["display_name"],
                    "mission_profile_id": requirement["profile_id"],
                    "mission_profile": requirement["name"],
                    "mission_distance_km": requirement["distance_km"],
                    "required_pack_specific_energy_Wh_kg": required,
                    "engineering_bounded_pack_Wh_kg": pack_energy,
                    "gap_to_requirement_Wh_kg": round(gap, 3) if gap is not None else None,
                    "battery_sufficiency_index": (
                        round(sufficiency, 5) if sufficiency is not None else None
                    ),
                    "diagnostic_status": status,
                    "performance_evidence": False,
                    "audited_measurement": False,
                    "ranking_evidence": False,
                    "claim_boundary": (
                        "Screening diagnostic only; does not validate material, "
                        "cell, pack, aircraft, or certification performance."
                    ),
                }
            )
    return rows


def _materials_project_snapshot(registries: Registries) -> dict[str, Any]:
    execute = bool(os.environ.get("MP_API_KEY"))
    result = dry_run_source(
        registries,
        "datasource.materials_project",
        query=MATERIALS_PROJECT_QUERY,
        rows=MATERIALS_PROJECT_ROWS,
        execute=execute,
    )
    return {
        "artifact_type": "materials_project_material_screening_metadata_snapshot",
        "status": result["status"],
        "execute_requested": execute,
        "executed": result["executed"],
        "source_id": result["source_id"],
        "query": result["query"],
        "row_count": result["record_count"],
        "license_status": result["license_status"],
        "metadata_only": True,
        "performance_evidence": False,
        "audited_measurement": False,
        "ranking_evidence": False,
        "requires_key": result["requires_key"],
        "key_env": result["key_env"],
        "credential_available": result["credential_available"],
        "limitations": [
            "Materials Project metadata can enrich composition/property context only.",
            "Materials Project rows are not battery performance measurements.",
            "No Materials Project metadata may appear in audited measurement views.",
        ],
        "error_message": result.get("error_message"),
        "records": result["records"],
        "request": result["request"],
    }


def _summary(
    cards: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
    mp_snapshot: dict[str, Any],
) -> dict[str, Any]:
    estimated_cards = [
        card
        for card in cards
        if card["engineering_bounded_pack_Wh_kg"] is not None
    ]
    theoretical_pack_values = [
        float(card["theoretical_only_pack_Wh_kg"])
        for card in cards
        if card["theoretical_only_pack_Wh_kg"] is not None
    ]
    engineered_pack_values = [
        float(card["engineering_bounded_pack_Wh_kg"])
        for card in estimated_cards
    ]
    diagnostic_meets = sum(
        row["diagnostic_status"] == "diagnostic_meets_or_exceeds_requirement"
        for row in gap_rows
    )
    return {
        "phase": "4.6",
        "phase_status": "material hypothesis screening active",
        "artifact_type": "material_screening_summary",
        "campaign_status": "generated",
        "simulation_only": True,
        "technology_readiness_claim": False,
        "performance_evidence": False,
        "audited_measurements": 0,
        "ranking_enabled": False,
        "material_candidate_count": len(cards),
        "energy_estimated_candidate_count": len(estimated_cards),
        "energy_blocked_candidate_count": len(cards) - len(estimated_cards),
        "frontier_gap_row_count": len(gap_rows),
        "diagnostic_requirement_meets_count": diagnostic_meets,
        "highest_theoretical_only_pack_Wh_kg": max(
            theoretical_pack_values,
            default=None,
        ),
        "highest_engineering_bounded_pack_Wh_kg": max(
            engineered_pack_values,
            default=None,
        ),
        "hemp_bast_fiber_candidate_present": any(
            "hemp" in card["material_id"] for card in cards
        ),
        "materials_project_status": mp_snapshot["status"],
        "materials_project_record_count": mp_snapshot["row_count"],
        "evidence_lanes": [
            "audited experimental measurements",
            "parsed but blocked/quality-review measurements",
            "local physics simulations",
            "material hypothesis screening",
            "speculative/theoretical stress tests",
        ],
        "what_would_need_to_be_true": [
            "Comparable full-cell measurements need uncertainty and system boundaries.",
            "Pack mass accounting must include containment, thermal control, reserve, "
            "degradation, interconnect, and certification margins.",
            "Material hypotheses need reproducible synthesis, cell build details, "
            "cycle life, abuse response, and aviation duty-cycle tests.",
            "Hemp/bast-fiber carbon needs primary measurements and full-cell translation "
            "before any aviation battery performance claim.",
            "Materials Project metadata needs experimental battery validation before "
            "it can influence performance evidence or ranking.",
        ],
    }


def build_materials_campaign(
    registries: Registries | None = None,
) -> dict[str, Any]:
    active_registries = registries or load_registries()
    cards = [_screen_material(candidate) for candidate in active_registries.material_candidates]
    requirements = _mission_requirements()
    gap_rows = _frontier_gap_rows(cards, requirements)
    mp_snapshot = _materials_project_snapshot(active_registries)
    summary = _summary(cards, gap_rows, mp_snapshot)
    payload = {
        "artifact_type": "materials_campaign",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "claim_boundary": (
            "Material screening is assumption-based hypothesis triage only. It is not "
            "experimental validation, DFT proof, pack proof, aircraft design, or "
            "candidate ranking."
        ),
        "summary": summary,
        "mission_requirements": requirements,
        "material_candidate_cards": cards,
        "material_frontier_gap": gap_rows,
        "materials_project_metadata": mp_snapshot,
        "limitations": [
            "No material card is an audited measurement.",
            "Rows missing voltage or capacity are intentionally blocked from energy estimates.",
            "Engineering-bounded pack values are assumption diagnostics, not achieved performance.",
            "Speculative carbon architectures, including hemp/bast-fiber carbon, "
            "are hypothesis tracking only.",
        ],
    }
    payload["payload_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return payload


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _artifact_record(path: Path, row_count: int | None = None) -> dict[str, Any]:
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "sha256": sha256_file(path),
        "row_count": row_count,
    }


def _write_markdown_summary(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Material Screening Summary",
        "",
        "> Hypothesis screening only. Not DFT proof, experimental validation,",
        "> pack proof, aircraft design, certification evidence, or ranking.",
        "",
        "## Status",
        "",
        f"- Phase lane: {summary['phase']}",
        f"- Material candidates: {summary['material_candidate_count']}",
        f"- Energy-estimated candidates: {summary['energy_estimated_candidate_count']}",
        f"- Energy-blocked candidates: {summary['energy_blocked_candidate_count']}",
        f"- Frontier gap rows: {summary['frontier_gap_row_count']}",
        (
            "- Highest theoretical-only pack estimate: "
            f"{summary['highest_theoretical_only_pack_Wh_kg']} Wh/kg"
        ),
        (
            "- Highest engineering-bounded pack estimate: "
            f"{summary['highest_engineering_bounded_pack_Wh_kg']} Wh/kg"
        ),
        f"- Materials Project status: {summary['materials_project_status']}",
        f"- Ranking enabled: {summary['ranking_enabled']}",
        "",
        "## Evidence Lanes",
        "",
    ]
    lines.extend(f"- {lane}" for lane in summary["evidence_lanes"])
    lines.extend(
        [
            "",
            "## What Would Need To Be True",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["what_would_need_to_be_true"])
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Material hypotheses cannot appear as audited measurements.",
            "- Materials Project metadata cannot become performance evidence.",
            "- Hemp/bast-fiber-derived graphene-like carbon remains exploratory "
            "carbon architecture only.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_materials_campaign(
    *,
    output_dir: Path | None = None,
) -> tuple[Path, Path, dict[str, Path]]:
    destination = output_dir or DEFAULT_MATERIALS_DIR
    destination.mkdir(parents=True, exist_ok=True)
    payload = build_materials_campaign()

    summary_path = destination / "material_screening_summary.json"
    markdown_path = destination / "material_screening_summary.md"
    cards_path = destination / "material_candidate_cards.json"
    gap_path = destination / "material_frontier_gap.json"
    mp_path = destination / "materials_project_metadata_snapshot.json"

    _write_json(
        cards_path,
        {
            "artifact_type": "material_candidate_cards",
            "row_count": len(payload["material_candidate_cards"]),
            "rows": payload["material_candidate_cards"],
        },
    )
    _write_json(
        gap_path,
        {
            "artifact_type": "material_frontier_gap",
            "row_count": len(payload["material_frontier_gap"]),
            "rows": payload["material_frontier_gap"],
        },
    )
    _write_json(mp_path, payload["materials_project_metadata"])
    artifacts = {
        "material_candidate_cards_json": _artifact_record(
            cards_path,
            len(payload["material_candidate_cards"]),
        ),
        "material_frontier_gap_json": _artifact_record(
            gap_path,
            len(payload["material_frontier_gap"]),
        ),
        "materials_project_metadata_snapshot_json": _artifact_record(
            mp_path,
            payload["materials_project_metadata"]["row_count"],
        ),
    }
    summary_payload = {**payload, "artifacts": artifacts}
    _write_json(summary_path, summary_payload)
    _write_markdown_summary(summary_payload, markdown_path)
    return (
        summary_path,
        markdown_path,
        {
            "material_candidate_cards_json": cards_path,
            "material_frontier_gap_json": gap_path,
            "materials_project_metadata_snapshot_json": mp_path,
        },
    )
