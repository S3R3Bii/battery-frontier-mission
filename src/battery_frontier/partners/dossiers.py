from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.measurements.cmu_evtol import (
    DEFAULT_MEASUREMENT_DIR,
    MEASUREMENT_SUMMARY_NAME,
    RAW_MANIFEST_NAME,
)
from battery_frontier.provenance import sha256_file
from battery_frontier.registry import load_registries

DEFAULT_PARTNER_DIR = PROJECT_ROOT / "reports" / "partners"
PARTNER_AUDIENCES = {
    "plane_manufacturer_dossier": "Plane Manufacturer Dossier",
    "battery_manufacturer_dossier": "Battery Manufacturer Dossier",
    "propulsion_partner_dossier": "Propulsion Partner Dossier",
    "research_partner_dossier": "Research Partner Dossier",
    "investor_or_program_manager_brief": "Investor or Program Manager Brief",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return {
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def _artifact_hashes() -> dict[str, dict[str, Any]]:
    candidates = {
        "simulation_campaign": PROJECT_ROOT
        / "reports"
        / "simulations"
        / "simulation_campaign_summary.json",
        "long_haul_feasibility": PROJECT_ROOT
        / "reports"
        / "simulations"
        / "long_haul_feasibility.json",
        "candidate_dossiers": PROJECT_ROOT / "reports" / "candidates" / "candidate_dossiers.json",
        "cmu_raw_manifest": DEFAULT_MEASUREMENT_DIR / RAW_MANIFEST_NAME,
        "cmu_measurement_summary": DEFAULT_MEASUREMENT_DIR / MEASUREMENT_SUMMARY_NAME,
    }
    return {
        key: artifact
        for key, path in candidates.items()
        if (artifact := _artifact(path)) is not None
    }


def _input_signature(payload: dict[str, Any]) -> str:
    stable = {
        "registry_counts": payload["registry_counts"],
        "measurement_status": payload["measurement_status"],
        "long_haul_status": payload["long_haul_status"],
        "dossier_ids": sorted(payload["dossiers"]),
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _shared_context() -> dict[str, Any]:
    registries = load_registries()
    simulation_path = PROJECT_ROOT / "reports" / "simulations" / "simulation_campaign_summary.json"
    long_haul_path = PROJECT_ROOT / "reports" / "simulations" / "long_haul_feasibility.json"
    raw_manifest_path = DEFAULT_MEASUREMENT_DIR / RAW_MANIFEST_NAME
    measurement_path = DEFAULT_MEASUREMENT_DIR / MEASUREMENT_SUMMARY_NAME
    candidate_path = PROJECT_ROOT / "reports" / "candidates" / "candidate_dossiers.json"

    simulation = _read_json(simulation_path)
    long_haul = _read_json(long_haul_path)
    raw_manifest = _read_json(raw_manifest_path)
    measurement = _read_json(measurement_path)
    candidates = _read_json(candidate_path)

    measurement_status = {
        "approved_source": "CMU eVTOL Battery Dataset",
        "raw_manifest_present": raw_manifest is not None,
        "measurement_summary_present": measurement is not None,
        "quality_status": measurement.get("quality_status") if measurement else "not_parsed",
        "audited_measurement_summary": (
            bool(measurement.get("audited_measurement_summary")) if measurement else False
        ),
        "system_boundary": (
            measurement.get("system_boundary")
            if measurement
            else "cell-level source approved; parsed measurements pending"
        ),
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "raw_files_committed": (
            bool(raw_manifest.get("raw_files_committed")) if raw_manifest else False
        ),
    }
    long_haul_rows = long_haul.get("rows", []) if long_haul else []
    long_haul_status = {
        "row_count": len(long_haul_rows),
        "infeasible_count": sum(not row.get("feasible", False) for row in long_haul_rows),
        "longest_case": max(
            (row.get("distance_km", 0) for row in long_haul_rows),
            default=None,
        ),
        "claim_boundary": "simulation diagnostic only",
    }
    return {
        "generated_at_utc": _utc_now(),
        "package_version": __version__,
        "registry_counts": registries.summary(),
        "phase": "4.5",
        "phase_status": (
            "dashboard and simulation automation active; experimental parsing is emerging"
        ),
        "scientific_guardrail": (
            "Do not treat metadata, fixtures, simulations, or cell-level data as "
            "pack-level validated aviation battery performance."
        ),
        "manufacturer_examples": [
            record.model_dump(mode="json") for record in registries.aircraft_systems
        ],
        "propulsion_examples": [
            record.model_dump(mode="json") for record in registries.propulsion_systems
        ],
        "dataset_candidates": [
            record.model_dump(mode="json") for record in registries.dataset_candidates
        ],
        "simulation_summary": simulation.get("summary") if simulation else None,
        "long_haul_rows": long_haul_rows,
        "candidate_summary": candidates.get("summary") if candidates else None,
        "measurement_status": measurement_status,
        "measurement_summary": measurement,
        "raw_manifest_summary": (
            {
                "selected_file_count": raw_manifest.get("selected_file_count"),
                "selected_size_bytes": raw_manifest.get("selected_size_bytes"),
                "downloaded_size_bytes": raw_manifest.get("downloaded_size_bytes"),
                "status_counts": raw_manifest.get("status_counts"),
                "raw_files_committed": raw_manifest.get("raw_files_committed"),
            }
            if raw_manifest
            else None
        ),
        "long_haul_status": long_haul_status,
        "artifact_hashes": _artifact_hashes(),
        "evidence_boundary": {
            "experimentally_measured": (
                "CMU source is approved; measurement values count only after parser "
                "and unit checks pass."
            ),
            "simulation_only": (
                "Aviation grid, long-haul stress tests, candidate envelopes, and pack "
                "trade space are diagnostics."
            ),
            "unknown": (
                "Comparable pack-level aviation measurements, safety, degradation, "
                "thermal transients, cost, and manufacturability remain open."
            ),
            "ranking": "disabled",
        },
    }


def _dossier_payload(audience_id: str, title: str, context: dict[str, Any]) -> dict[str, Any]:
    asks_by_audience = {
        "plane_manufacturer_dossier": [
            "Provide aircraft-level mission assumptions with payload, reserve, "
            "pack mass, and thermal boundaries.",
            "Share non-proprietary pack-energy and power envelopes for reproducibility checks.",
            "Help validate mission profiles against aircraft design studies without tuning.",
        ],
        "battery_manufacturer_dossier": [
            "Provide audited cell and pack data with uncertainty, test protocol, "
            "and mass boundary.",
            "Map safety, abuse, cycle-life, and thermal data to aviation-relevant duty cycles.",
            "Separate cell performance from module and pack overhead in reported evidence.",
        ],
        "propulsion_partner_dossier": [
            "Provide motor and propulsor power envelopes with transient duty-cycle boundaries.",
            "Help map propulsion loads to battery C-rate, thermal, and reserve requirements.",
            "Identify where hydrogen-electric, hybrid, and battery-only boundaries diverge.",
        ],
        "research_partner_dossier": [
            "Contribute license-cleared datasets with schemas, units, uncertainty, and provenance.",
            "Help normalize impedance, capacity, temperature, and duty-cycle "
            "fields across datasets.",
            "Audit edge cases that could promote metadata or fixtures into measurement views.",
        ],
        "investor_or_program_manager_brief": [
            "Fund data curation, parser audits, and reproducible external "
            "validation before scoring.",
            "Prioritize pack-level safety and thermal evidence over unsupported "
            "energy-density claims.",
            "Track phase gates by evidence readiness rather than optimistic leaderboard progress.",
        ],
    }
    focus_by_audience = {
        "plane_manufacturer_dossier": [
            "aviation requirement gap",
            "long-haul infeasibility reasons",
            "manufacturer example boundaries",
        ],
        "battery_manufacturer_dossier": [
            "CMU cell-level ingestion pipeline",
            "pack-overhead and cell-to-pack translation",
            "missing uncertainty and safety evidence",
        ],
        "propulsion_partner_dossier": [
            "propulsion system registry",
            "power and C-rate diagnostics",
            "battery sufficiency under mission loads",
        ],
        "research_partner_dossier": [
            "dataset triage queue",
            "measurement schema and quality checks",
            "license and provenance requirements",
        ],
        "investor_or_program_manager_brief": [
            "phase status",
            "evidence blockers",
            "automation and reporting readiness",
        ],
    }
    blockers = [
        "No comparable audited pack-level aviation battery measurements are available.",
        "CMU eVTOL source is cell-level evidence and cannot prove pack sufficiency.",
        "Manufacturer examples are context records with mixed official/third-party boundaries.",
        "Long-haul feasibility remains simulation-only and expected-infeasible "
        "under current assumptions.",
        "Candidate ranking is blocked until uncertainty, safety, cycle-life, "
        "and system boundaries are audited.",
    ]
    return {
        "artifact_type": "partner_dossier",
        "audience_id": audience_id,
        "title": title,
        "generated_at_utc": context["generated_at_utc"],
        "package_version": context["package_version"],
        "phase": context["phase"],
        "phase_status": context["phase_status"],
        "focus": focus_by_audience[audience_id],
        "what_the_platform_currently_knows": {
            "registry_counts": context["registry_counts"],
            "manufacturer_examples": context["manufacturer_examples"],
            "propulsion_examples": context["propulsion_examples"],
            "dataset_candidates": context["dataset_candidates"],
            "simulation_summary": context["simulation_summary"],
            "long_haul_status": context["long_haul_status"],
            "measurement_status": context["measurement_status"],
        },
        "simulation_only": {
            "aviation_requirement_grid": (
                context["simulation_summary"]["aviation_requirement_grid_rows"]
                if context["simulation_summary"]
                else 0
            ),
            "pack_trade_space": (
                context["simulation_summary"]["pack_trade_space_rows"]
                if context["simulation_summary"]
                else 0
            ),
            "long_haul_feasibility": context["long_haul_rows"],
        },
        "experimentally_measured": context["measurement_status"],
        "what_remains_unknown": blockers,
        "current_aviation_battery_gap": {
            "central_message": (
                "Known audited comparable performance is not yet populated; mission "
                "requirements and simulations define the gap envelope."
            ),
            "ranking_enabled": False,
            "battery_sufficiency_index_boundary": (
                "model diagnostic only, not a real technology score"
            ),
        },
        "dataset_status": {
            "approved_source": context["measurement_status"],
            "candidate_dataset_count": len(context["dataset_candidates"]),
            "raw_manifest_summary": context["raw_manifest_summary"],
        },
        "manufacturer_example_table": context["manufacturer_examples"],
        "propulsion_example_table": context["propulsion_examples"],
        "feasibility_blockers": blockers,
        "proposed_collaboration_asks": asks_by_audience[audience_id],
        "exact_evidence_boundary": context["evidence_boundary"],
        "artifact_hashes": context["artifact_hashes"],
        "claim_boundary": context["scientific_guardrail"],
    }


def build_partner_dossiers() -> dict[str, Any]:
    context = _shared_context()
    dossiers = {
        audience_id: _dossier_payload(audience_id, title, context)
        for audience_id, title in PARTNER_AUDIENCES.items()
    }
    payload = {
        "artifact_type": "partner_dossier_bundle",
        "generated_at_utc": context["generated_at_utc"],
        "package_version": context["package_version"],
        "phase": context["phase"],
        "phase_status": context["phase_status"],
        "dossier_count": len(dossiers),
        "dossiers": dossiers,
        "registry_counts": context["registry_counts"],
        "artifact_hashes": context["artifact_hashes"],
        "measurement_status": context["measurement_status"],
        "long_haul_status": context["long_haul_status"],
        "significant_change_policy": [
            "new approved source",
            "new parsed measurement batch",
            "new manufacturer/system registry entries",
            ">5% change in requirement envelope",
            "new infeasible/feasible boundary shift",
            "new partner dossier hash",
        ],
    }
    payload["input_signature_sha256"] = _input_signature(payload)
    return payload


def _write_dossier_markdown(payload: dict[str, Any], target: Path) -> None:
    lines = [
        f"# {payload['title']}",
        "",
        "> Factual partner brief. Simulations, metadata, and cell-level evidence are",
        "> clearly separated from pack-level validation.",
        "",
        "## Boundary",
        "",
        f"- Phase: {payload['phase']} - {payload['phase_status']}",
        f"- Claim boundary: {payload['claim_boundary']}",
        f"- Ranking enabled: {payload['current_aviation_battery_gap']['ranking_enabled']}",
        "",
        "## Current Signal",
        "",
        f"- Aircraft examples: {len(payload['manufacturer_example_table'])}",
        f"- Propulsion examples: {len(payload['propulsion_example_table'])}",
        f"- Dataset candidates: {payload['dataset_status']['candidate_dataset_count']}",
        "- CMU measurement status: "
        f"{payload['experimentally_measured']['quality_status']}",
        "- Long-haul infeasible cases: "
        f"{payload['what_the_platform_currently_knows']['long_haul_status']['infeasible_count']}",
        "",
        "## Feasibility Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["feasibility_blockers"])
    lines.extend(["", "## Collaboration Asks", ""])
    lines.extend(f"- {item}" for item in payload["proposed_collaboration_asks"])
    lines.extend(
        [
            "",
            "## Artifact Hashes",
            "",
        ]
    )
    for artifact_id, artifact in payload["artifact_hashes"].items():
        lines.append(f"- `{artifact_id}`: `{artifact['sha256']}` (`{artifact['path']}`)")
    target.write_text("\n".join(lines), encoding="utf-8")


def _write_latest(payload: dict[str, Any], latest_dir: Path) -> dict[str, dict[str, Any]]:
    latest_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict[str, Any]] = {}
    for audience_id, dossier in payload["dossiers"].items():
        json_path = latest_dir / f"{audience_id}.json"
        md_path = latest_dir / f"{audience_id}.md"
        json_path.write_text(json.dumps(dossier, indent=2, sort_keys=True), encoding="utf-8")
        _write_dossier_markdown(dossier, md_path)
        written[audience_id] = {
            "json": _artifact(json_path),
            "markdown": _artifact(md_path),
        }
    return written


def _archive_latest(latest_dir: Path, archive_root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = archive_root / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in latest_dir.glob("*"):
        if path.is_file():
            shutil.copy2(path, archive_dir / path.name)
    return archive_dir


def write_partner_dossiers(*, output_dir: Path | None = None) -> tuple[Path, Path | None]:
    destination = output_dir or DEFAULT_PARTNER_DIR
    latest_dir = destination / "latest"
    archive_root = destination / "archive"
    destination.mkdir(parents=True, exist_ok=True)

    payload = build_partner_dossiers()
    existing_manifest = _read_json(latest_dir / "partner_dossiers_manifest.json")
    should_archive = (
        existing_manifest is None
        or existing_manifest.get("input_signature_sha256")
        != payload["input_signature_sha256"]
    )
    written = _write_latest(payload, latest_dir)
    manifest = {
        **payload,
        "written_artifacts": written,
        "archive_created": should_archive,
        "archive_reason": (
            "input signature changed or first partner dossier run"
            if should_archive
            else "no significant input change"
        ),
    }
    manifest_path = latest_dir / "partner_dossiers_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    archive_dir = _archive_latest(latest_dir, archive_root) if should_archive else None
    return manifest_path, archive_dir
