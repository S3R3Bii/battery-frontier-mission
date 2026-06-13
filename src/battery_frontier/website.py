from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
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
from battery_frontier.registry import load_registries
from battery_frontier.scientific_audit import evaluate_ranking_gate


def _records(frame: Any) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records"))


def _latest_daily_manifest() -> dict[str, Any] | None:
    daily_dir = PROJECT_ROOT / "reports" / "daily"
    manifests = sorted(daily_dir.glob("*-mission-report.json"))
    if not manifests:
        return None
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


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
        "audited_measurements": 0,
        "metrics": {
            "assumptions": len(registries.assumptions),
            "chemistry_families": len(registries.chemistries),
            "citations": len(registries.citations),
            "data_sources": len(registries.data_sources),
            "physics_fixtures": len(registries.physics_reference_cases),
            "mission_fixtures": len(registries.segmented_mission_cases),
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
