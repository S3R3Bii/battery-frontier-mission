from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.candidates.dossiers import build_candidate_dossiers
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.dashboards.data import (
    chemistry_readiness_frame,
    evidence_ledger_frame,
    load_dashboard_bundle,
    phase_readiness_frame,
    physics_boundary_frame,
    source_readiness_frame,
    verify_dashboard_artifacts,
)
from battery_frontier.data.connectors import source_status_rows
from battery_frontier.materials.campaign import build_materials_campaign
from battery_frontier.registry import load_registries
from battery_frontier.scientific_audit import evaluate_ranking_gate
from battery_frontier.simulations.campaign import build_simulation_campaign


def _records(frame: Any) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records"))


def _latest_daily_manifest() -> dict[str, Any] | None:
    daily_dir = PROJECT_ROOT / "reports" / "daily"
    manifests = sorted(daily_dir.glob("*-mission-report.json"))
    if not manifests:
        return None
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_dossier_payload() -> dict[str, Any]:
    path = PROJECT_ROOT / "reports" / "candidates" / "candidate_dossiers.json"
    return _read_json_if_exists(path) or build_candidate_dossiers(
        execute_materials_project=False
    )


def _simulation_campaign_payload() -> dict[str, Any]:
    path = PROJECT_ROOT / "reports" / "simulations" / "simulation_campaign_summary.json"
    return _read_json_if_exists(path) or build_simulation_campaign()


def _materials_campaign_payload() -> dict[str, Any]:
    path = PROJECT_ROOT / "reports" / "materials" / "material_screening_summary.json"
    return _read_json_if_exists(path) or build_materials_campaign()


def _measurement_payloads() -> dict[str, Any]:
    measurement_dir = PROJECT_ROOT / "reports" / "measurements"
    raw_manifest = _read_json_if_exists(measurement_dir / "cmu_evtol_raw_file_manifest.json")
    measurement_summary = _read_json_if_exists(
        measurement_dir / "cmu_evtol_measurement_summary.json"
    )
    audited_count = 0
    if measurement_summary and measurement_summary.get("quality_status") == "passed":
        audited_count = int(measurement_summary.get("timeseries_file_count", 0)) + int(
            measurement_summary.get("impedance_file_count", 0)
        )
    return {
        "raw_manifest": raw_manifest,
        "measurement_summary": measurement_summary,
        "audited_measurement_count": audited_count,
    }


def _partner_dossier_payload() -> dict[str, Any] | None:
    return _read_json_if_exists(
        PROJECT_ROOT / "reports" / "partners" / "latest" / "partner_dossiers_manifest.json"
    )


def _conceptual_target_system() -> dict[str, Any]:
    return {
        "title": "Long-Term Conceptual Target Aircraft",
        "status": "mission reminder only",
        "claim_boundary": (
            "Speculative systems diagram for dashboard orientation. Not an aircraft "
            "design, certification claim, performance result, or build blueprint."
        ),
        "labels": [
            {
                "name": "Distributed electric propulsion",
                "status": "concept placeholder; no propulsion sizing claim",
            },
            {
                "name": "Aviation-grade battery pack corridor",
                "status": "target boundary; no validated pack exists in this repo",
            },
            {
                "name": "Thermal and containment loop",
                "status": "required subsystem; not yet simulated with transients",
            },
            {
                "name": "Payload and reserve margin",
                "status": "mission-model boundary; certification rules not modeled",
            },
            {
                "name": "Structural integration option",
                "status": "research concept; damage tolerance not established",
            },
        ],
    }


def _frontier_points(bundle: Any) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = [
        {
            "label": "Audited comparable measurements",
            "lane": "audited measurements",
            "specific_energy_Wh_kg": None,
            "evidence": "not_available",
            "boundary": "cell or pack",
            "status": "blocked until licensed records are ingested",
            "publication_allowed": False,
        }
    ]
    for row in _records(physics_boundary_frame(bundle)):
        points.append(
            {
                "label": row["case"],
                "lane": "local calculation fixture",
                "specific_energy_Wh_kg": row["specific energy (Wh/kg)"],
                "evidence": row["evidence"],
                "boundary": row["boundary"],
                "status": "fixture only; not experimental evidence",
                "publication_allowed": True,
            }
        )
    for case in bundle.aviation["cases"]:
        points.append(
            {
                "label": case["name"],
                "lane": "mission pack input",
                "specific_energy_Wh_kg": case.get("configured_pack_specific_energy_Wh_kg"),
                "evidence": case["evidence_class"],
                "boundary": "pack-level mission input",
                "status": "feasible fixture" if case["feasible"] else "infeasible fixture",
                "publication_allowed": True,
            }
        )
    return points


def _mission_bands(bundle: Any) -> list[dict[str, Any]]:
    bands = []
    for case in bundle.aviation["cases"]:
        configured = case.get("configured_pack_specific_energy_Wh_kg")
        if configured is None:
            continue
        bands.append(
            {
                "label": case["name"],
                "pack_specific_energy_Wh_kg": configured,
                "feasible": case["feasible"],
                "converged": case["converged"],
                "status": case["status"],
                "evidence": case["evidence_class"],
                "claim_boundary": "configured Phase 3 input, not validated requirement",
            }
        )
    return bands


def build_website_data() -> dict[str, Any]:
    registries = load_registries()
    bundle = load_dashboard_bundle()
    verification = verify_dashboard_artifacts(bundle)
    gate = evaluate_ranking_gate([])
    verified_count = int(verification["hash_matches"].sum())
    phase_rows = _records(phase_readiness_frame(registries))
    source_rows = _records(source_readiness_frame(registries))
    connector_rows = source_status_rows(registries)
    candidate_payload = _candidate_dossier_payload()
    simulation_payload = _simulation_campaign_payload()
    materials_payload = _materials_campaign_payload()
    measurement_payload = _measurement_payloads()
    partner_payload = _partner_dossier_payload()
    simulation_summary = simulation_payload["summary"]
    materials_summary = materials_payload["summary"]
    audited_measurements = measurement_payload["audited_measurement_count"]
    mission_bands = _mission_bands(bundle)
    physics_points = [
        point
        for point in _frontier_points(bundle)
        if point["lane"] == "local calculation fixture"
        and point["boundary"] == "complete pack"
        and point["specific_energy_Wh_kg"] is not None
    ]
    best_fixture_pack = max(
        (point["specific_energy_Wh_kg"] for point in physics_points),
        default=None,
    )
    max_mission_input = max(
        (band["pack_specific_energy_Wh_kg"] for band in mission_bands),
        default=None,
    )
    fixture_overlay_fraction = (
        min(best_fixture_pack / max_mission_input, 1.0)
        if best_fixture_pack is not None and max_mission_input
        else None
    )
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "phase": "4",
        "phase_status": "scientific dashboard prototype active",
        "technology_readiness_claim": False,
        "ranking_enabled": False,
        "ranking_gate_reason": gate.reason,
        "audited_measurements": audited_measurements,
        "metrics": {
            "assumptions": len(registries.assumptions),
            "chemistry_families": len(registries.chemistries),
            "citations": len(registries.citations),
            "data_sources": len(registries.data_sources),
            "aircraft_systems": len(registries.aircraft_systems),
            "propulsion_systems": len(registries.propulsion_systems),
            "dataset_candidates": len(registries.dataset_candidates),
            "material_candidates": len(registries.material_candidates),
            "physics_fixtures": len(registries.physics_reference_cases),
            "mission_fixtures": len(registries.segmented_mission_cases),
            "candidate_dossiers": candidate_payload["summary"]["candidate_count"],
            "partner_dossiers": (
                partner_payload["dossier_count"] if partner_payload else 0
            ),
            "simulation_rows": simulation_summary["aviation_requirement_grid_rows"]
            + simulation_summary["pack_trade_space_rows"]
            + simulation_summary["long_haul_study_count"],
            "long_haul_cases": simulation_summary["long_haul_study_count"],
            "material_gap_rows": materials_summary["frontier_gap_row_count"],
            "verified_artifacts": verified_count,
            "total_artifacts": len(verification),
        },
        "frontier": {
            "title": "Frontier Gap to Aviation-Grade Pack Energy",
            "audited_progress_fraction": None,
            "fixture_overlay_fraction": fixture_overlay_fraction,
            "best_fixture_pack_Wh_kg": best_fixture_pack,
            "max_configured_mission_input_Wh_kg": max_mission_input,
            "points": _frontier_points(bundle),
            "mission_bands": mission_bands,
            "unknown_region_note": (
                "The audited-measurement lane is empty; fixture values cannot be used "
                "as evidence of achieved aviation-grade storage."
            ),
        },
        "phase_readiness": phase_rows,
        "evidence_ledger": _records(evidence_ledger_frame(bundle)),
        "artifact_verification": _records(verification),
        "chemistry_readiness": _records(chemistry_readiness_frame(registries)),
        "source_readiness": source_rows,
        "connector_readiness": connector_rows,
        "candidate_dossiers": candidate_payload["dossiers"],
        "candidate_dossier_summary": candidate_payload["summary"],
        "candidate_ranking_missing_by_candidate": candidate_payload[
            "ranking_missing_by_candidate"
        ],
        "simulation_campaign_summary": simulation_summary,
        "measurement_pipeline": {
            "approved_source": {
                "source_id": "datasource.cmu_evtol_battery",
                "name": "Carnegie Mellon eVTOL Battery Dataset",
                "url": "https://kilthub.cmu.edu/articles/dataset/eVTOL_Battery_Dataset/14226830",
                "doi": "10.1184/R1/14226830",
                "license": "CC BY 4.0",
                "system_boundary": "cell-level eVTOL duty-cycle evidence only",
            },
            "raw_manifest_present": measurement_payload["raw_manifest"] is not None,
            "measurement_summary_present": (
                measurement_payload["measurement_summary"] is not None
            ),
            "raw_snapshot": {
                "selected_file_count": (
                    measurement_payload["raw_manifest"].get("selected_file_count")
                    if measurement_payload["raw_manifest"]
                    else 0
                ),
                "selected_size_bytes": (
                    measurement_payload["raw_manifest"].get("selected_size_bytes")
                    if measurement_payload["raw_manifest"]
                    else 0
                ),
                "downloaded_size_bytes": (
                    measurement_payload["raw_manifest"].get("downloaded_size_bytes")
                    if measurement_payload["raw_manifest"]
                    else 0
                ),
                "status_counts": (
                    measurement_payload["raw_manifest"].get("status_counts")
                    if measurement_payload["raw_manifest"]
                    else {}
                ),
                "raw_files_committed": (
                    measurement_payload["raw_manifest"].get("raw_files_committed")
                    if measurement_payload["raw_manifest"]
                    else False
                ),
            },
            "quality_report": measurement_payload["measurement_summary"],
            "audited_measurement_count": audited_measurements,
            "pack_level_evidence": False,
            "candidate_ranking_evidence": False,
            "claim_boundary": (
                "CMU source is approved experimental cell-level evidence. It is not "
                "pack-level proof or candidate-ranking evidence."
            ),
        },
        "aviation_requirement_map": {
            "row_count": len(simulation_payload["aviation_requirement_grid"]),
            "rows": simulation_payload["aviation_requirement_grid"],
        },
        "long_haul_feasibility": {
            "row_count": len(simulation_payload["long_haul_feasibility"]),
            "rows": simulation_payload["long_haul_feasibility"],
            "claim_boundary": "simulation diagnostic only, not an aircraft design.",
        },
        "manufacturer_examples": [
            record.model_dump(mode="json") for record in registries.aircraft_systems
        ],
        "propulsion_examples": [
            record.model_dump(mode="json") for record in registries.propulsion_systems
        ],
        "dataset_candidates": [
            record.model_dump(mode="json") for record in registries.dataset_candidates
        ],
        "partner_dossiers": partner_payload,
        "pack_trade_space_summary": {
            "row_count": simulation_summary["pack_trade_space_rows"],
            "infeasible_count": simulation_summary["pack_trade_infeasible_count"],
            "sensitivity": simulation_summary["pack_sensitivity"],
            "claim_boundary": (
                "Architecture sweep only; required cell energy is not a material claim."
            ),
        },
        "candidate_envelopes": simulation_payload["candidate_envelopes"],
        "materials_campaign_summary": materials_summary,
        "material_candidate_cards": materials_payload["material_candidate_cards"],
        "material_frontier_gap": materials_payload["material_frontier_gap"],
        "material_mission_requirements": materials_payload["mission_requirements"],
        "material_metadata_snapshot": materials_payload["materials_project_metadata"],
        "infeasible_region_ledger": simulation_summary["infeasible_region_ledger"],
        "what_would_need_to_be_true": simulation_summary["what_would_need_to_be_true"],
        "materials_project_appendix": {
            "artifact_type": candidate_payload["materials_project_appendix"][
                "artifact_type"
            ],
            "query_count": candidate_payload["materials_project_appendix"]["query_count"],
            "record_count": candidate_payload["materials_project_appendix"]["record_count"],
            "status_counts": candidate_payload["materials_project_appendix"][
                "status_counts"
            ],
            "ranking_evidence": candidate_payload["materials_project_appendix"][
                "ranking_evidence"
            ],
            "performance_evidence": candidate_payload["materials_project_appendix"][
                "performance_evidence"
            ],
            "queries": [
                {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "label": query["label"],
                    "status": query["status"],
                    "record_count": query["record_count"],
                    "candidate_ids": query["candidate_ids"],
                    "material_ids": query["material_ids"],
                    "error_message": query.get("error_message"),
                }
                for query in candidate_payload["materials_project_appendix"]["queries"]
            ],
            "limitations": candidate_payload["materials_project_appendix"][
                "limitations"
            ],
        },
        "conceptual_target_system": _conceptual_target_system(),
        "latest_daily_manifest": _latest_daily_manifest(),
        "dashboard_manifest": bundle.manifest,
    }


def export_website_data(output_path: Path | None = None) -> Path:
    target = output_path or PROJECT_ROOT / "website" / "mission-control-data.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_website_data(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target
