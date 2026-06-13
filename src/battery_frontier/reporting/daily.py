from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from battery_frontier import __version__
from battery_frontier.aviation.reference_cases import calculate_all_mission_cases
from battery_frontier.candidates.dossiers import build_candidate_dossiers
from battery_frontier.config import CONFIG_DIR, PROJECT_ROOT
from battery_frontier.data.connectors import source_status_rows
from battery_frontier.provenance import hash_files, sha256_file
from battery_frontier.registry import load_registries
from battery_frontier.reporting.method_cards import generate_dashboard_artifacts
from battery_frontier.simulations.campaign import build_simulation_campaign


def _markdown_hashes(hashes: dict[str, str]) -> str:
    return "\n".join(f"- `{name}`: `{digest}`" for name, digest in hashes.items())


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _candidate_payload() -> tuple[dict, Path | None]:
    path = PROJECT_ROOT / "reports" / "candidates" / "candidate_dossiers.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), path
    return build_candidate_dossiers(execute_materials_project=False), None


def _simulation_payload() -> tuple[dict, Path | None]:
    path = PROJECT_ROOT / "reports" / "simulations" / "simulation_campaign_summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), path
    return build_simulation_campaign(), None


def generate_daily_report(
    report_date: date | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    registries = load_registries()
    effective_date = report_date or date.today()
    destination = output_dir or PROJECT_ROOT / "reports" / "daily"
    destination.mkdir(parents=True, exist_ok=True)
    config_paths = list(CONFIG_DIR.glob("*.yaml"))
    config_hashes = hash_files(config_paths, PROJECT_ROOT)
    code_paths = [
        *PROJECT_ROOT.glob("src/**/*.py"),
        *PROJECT_ROOT.glob("dashboard/**/*.py"),
        *PROJECT_ROOT.glob("schemas/*.sql"),
    ]
    code_hashes = hash_files(code_paths, PROJECT_ROOT)
    code_snapshot_sha256 = hashlib.sha256(
        json.dumps(code_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()

    report_path = destination / f"{effective_date.isoformat()}-mission-report.md"
    manifest_path = destination / f"{effective_date.isoformat()}-mission-report.json"
    summary_path = destination / f"{effective_date.isoformat()}-mission-summary.json"
    source_status = {
        source.ingestion_status: sum(
            candidate.ingestion_status == source.ingestion_status
            for candidate in registries.data_sources
        )
        for source in registries.data_sources
    }
    mission_results = calculate_all_mission_cases(registries.segmented_mission_cases)
    feasible_missions = sum(result["feasible"] for result in mission_results)
    dashboard_manifest_path, dashboard_artifacts = generate_dashboard_artifacts()
    candidate_payload, candidate_path = _candidate_payload()
    candidate_summary = candidate_payload["summary"]
    candidate_sha256 = sha256_file(candidate_path) if candidate_path else None
    materials_project_appendix = candidate_summary["materials_project_appendix"]
    blocked_candidate_count = candidate_summary["ranking_blocked_candidate_count"]
    mp_record_count = materials_project_appendix["record_count"]
    candidate_artifact = _display_path(candidate_path) if candidate_path else "not yet written"
    simulation_payload, simulation_path = _simulation_payload()
    simulation_summary = simulation_payload["summary"]
    simulation_sha256 = sha256_file(simulation_path) if simulation_path else None
    simulation_artifact = (
        _display_path(simulation_path) if simulation_path else "not yet written"
    )
    connector_status = source_status_rows(registries)
    connector_ready = sum(row["execution_supported"] for row in connector_status)
    trusted_sources = sum(row["trusted_publication_allowed"] for row in connector_status)
    materials_project_status = next(
        (
            row["readiness"]
            for row in connector_status
            if row["source_id"] == "datasource.materials_project"
        ),
        "not registered",
    )
    artifact_rows = "\n".join(
        f"- `{artifact.artifact_id}`: `{artifact.sha256}`"
        for artifact in dashboard_artifacts
    )

    evidence_rows = "\n".join(
        [
            "| Faraday-law capacity equation implemented | theoretical_limit "
            "| reaction basis | constant plus declared mass basis | source code and tests |",
            "| Cruise mechanical-energy equation implemented | theoretical_limit "
            "| mission model | model-form uncertainty not yet quantified | source code and tests |",
            "| Aviation scenarios registered | speculative_hypothesis | mission "
            "| scenario note and sensitivity ranges | no external claim |",
            "| Phase 2 calculation fixtures | theoretical or speculative "
            "| reaction/cell/pack | deterministic intervals | source code and tests |",
            "| Phase 3 segmented mission fixtures | simulation_estimate "
            "| aircraft mission | sensitivity studies, not confidence intervals "
            "| source code and tests |",
            "| Phase 4 dashboard artifacts | public method and result artifacts "
            "| dashboard | SHA-256 integrity checks | dashboard manifest |",
        ]
    )

    report = f"""# Daily Mission Report - {effective_date.isoformat()}

> Phase: 4 scientific dashboard prototype active
>
> Evidence status: No experimental performance dataset has been ingested.
> Chemistry performance ranking is intentionally disabled.

## Public Summary

The Phase 0/1 scientific foundation, Phase 2 physics engine, and Phase 3 mission
model are established locally. Phase 4 now publishes traceable charts, evidence
readiness, downloadable method cards, and hashed result artifacts. Experimental
chemistry rankings remain blocked.

## What Changed

- Registered assumptions: {len(registries.assumptions)}
- Registered aviation design-study scenarios: {len(registries.scenarios)}
- Registered chemistry families awaiting comparable evidence: {len(registries.chemistries)}
- Candidate evidence dossiers: {candidate_summary["candidate_count"]}
- Registered citations and source records: {len(registries.citations)}
- Registered upstream data sources: {len(registries.data_sources)}
- Registered Phase 2 reference calculations: {len(registries.physics_reference_cases)}
- Registered Phase 3 mission calculations: {len(registries.segmented_mission_cases)}
- Phase 3 fixtures feasible under configured assumptions: {feasible_missions}
- Phase 4 downloadable artifacts: {len(dashboard_artifacts)}
- Experimental measurements ingested: 0
- Simulations completed: {len(mission_results)}
- Simulation campaign aviation grid rows: {simulation_summary["aviation_requirement_grid_rows"]}
- Simulation campaign pack trade rows: {simulation_summary["pack_trade_space_rows"]}
- Candidate rankings changed: 0

## Top Three Changed Findings

1. Physics and aviation outputs now have public method cards and manifest hashes.
2. Dashboard charts retain evidence class, system boundary, assumptions, and limitations.
3. Source readiness and missing experimental evidence are visible instead of
   being replaced with an unsupported chemistry leaderboard.
4. Candidate dossiers preserve promising leads, including hemp bast-fiber-derived
   graphitic carbon, without upgrading them into validated measurements.
5. The simulation campaign now maps aviation requirements, pack architecture
   penalties, candidate envelopes, and infeasible regions without creating
   experimental evidence.

## Evidence Ledger

| Finding | Evidence class | Boundary | Uncertainty | Citation or run |
| --- | --- | --- | --- | --- |
{evidence_rows}

## Source Readiness

```json
{json.dumps(source_status, indent=2, sort_keys=True)}
```

## Connector Readiness

- Metadata connectors with optional execution paths: {connector_ready}
- Sources approved for trusted published snapshots: {trusted_sources}
- Materials Project status: {materials_project_status}.
- CMU eVTOL battery status: approved CC BY 4.0 cell-level experimental source;
  metadata snapshot is allowed, but measured file ingestion still requires
  download, hashing, parsing, unit audit, and boundary mapping.
- NASA NTRS and OSTI status: metadata connectors are available; records remain
  metadata-only until reviewed.

## Dashboard Artifact Hashes

{artifact_rows}

## Assumption Changes

Phase 2 and Phase 3 fixtures remain versioned separately from empirical
measurements. Phase 4 displays those labels and verifies downloadable artifact
hashes; it does not upgrade simulations into facts.

## Candidate Screening

- Candidate dossiers: {candidate_summary["candidate_count"]}
- Ranking enabled: {candidate_summary["ranking_enabled"]}
- Ranking gate: {candidate_summary["ranking_gate_reason"]}
- Candidates blocked by missing ranking fields: {blocked_candidate_count}
- Materials Project metadata records linked as discovery context: {mp_record_count}
- Hemp bast-fiber graphitic carbon status: speculative material lead only; no
  audited full-cell, pack, cycle-life, safety, or aviation performance evidence.

Required experimental, uncertainty, safety, cycle-life, manufacturing, and
source-lineage fields are not yet populated for ranking.

## Simulation Campaign

- Campaign status: {simulation_summary["campaign_status"]}
- Simulation-only outputs: {simulation_summary["simulation_only"]}
- Aviation grid rows: {simulation_summary["aviation_requirement_grid_rows"]}
- Feasible aviation rows: {simulation_summary["aviation_feasible_count"]}
- Infeasible aviation rows: {simulation_summary["aviation_infeasible_count"]}
- Pack trade-space rows: {simulation_summary["pack_trade_space_rows"]}
- Pack rows above research ceiling: {simulation_summary["pack_trade_infeasible_count"]}
- Candidate envelopes: {simulation_summary["candidate_envelope_count"]}
- Experimental evidence created: no
- Ranking enabled by simulations: {simulation_summary["ranking_enabled"]}

```json
{json.dumps(simulation_summary["aviation_limiting_constraints"], indent=2, sort_keys=True)}
```

## Uncertainty and Reality Filter

Unknown performance remains unknown. Chemistry-family records identify required
metrics and known research constraints but contain no comparative scores.

## Failed or Rejected Hypotheses

None logged yet. The normalized schema includes a failed-hypothesis registry so
negative results remain public and reproducible.

## Next Work

1. Fetch and hash the approved CMU eVTOL dataset metadata snapshot.
2. Download the approved measurement archive only when storage/runtime budget is acceptable.
3. Parse a controlled subset of cell-level files and audit units, timestamps,
   capacity, current sign convention, temperature, and system boundary.
4. Audit a published full-reaction reference and define acceptance tolerance.
5. Reproduce one published aviation mission study without tuning discrepancies away.
6. Populate the dashboard with audited cell-level measurements and uncertainty.
7. Add segment power and thermal transients with visible model-form uncertainty.

## Reproducibility

- Package version: `{__version__}`
- Code snapshot SHA-256: `{code_snapshot_sha256}`
- Python: `{platform.python_version()}`
- Platform: `{platform.platform()}`
- Generated UTC: `{datetime.now(UTC).isoformat()}`
- Configuration hashes:
{_markdown_hashes(config_hashes)}
- Dashboard manifest: `{dashboard_manifest_path.relative_to(PROJECT_ROOT).as_posix()}`
- Candidate dossier artifact: `{candidate_artifact}`
- Candidate dossier SHA-256: `{candidate_sha256 or "not yet written"}`
- Simulation campaign artifact: `{simulation_artifact}`
- Simulation campaign SHA-256: `{simulation_sha256 or "not yet written"}`

## Limitations

This Phase 4 report contains no audited experimental battery performance or
validated aircraft mission record. Scenario outputs are unsuitable for design,
procurement, investment, operations, or certification decisions.
"""
    report_path.write_text(report, encoding="utf-8")

    summary = {
        "report_date": effective_date.isoformat(),
        "phase": "4",
        "phase_status": "scientific dashboard prototype active",
        "public_summary": (
            "Phase 4 is operational as a traceable dashboard prototype. "
            "No audited experimental battery-performance dataset is ingested, "
            "so chemistry ranking remains disabled."
        ),
        "ranking_enabled": False,
        "audited_measurements": 0,
        "feasible_mission_fixtures": feasible_missions,
        "simulation_fixtures": len(mission_results),
        "simulation_campaign": simulation_summary,
        "simulation_campaign_path": (
            _display_path(simulation_path) if simulation_path else None
        ),
        "simulation_campaign_sha256": simulation_sha256,
        "candidate_dossiers": candidate_summary["candidate_count"],
        "candidate_summary": candidate_summary,
        "source_status": source_status,
        "connector_readiness": connector_status,
        "dashboard_manifest": dashboard_manifest_path.relative_to(PROJECT_ROOT).as_posix(),
        "dashboard_manifest_sha256": sha256_file(dashboard_manifest_path),
        "candidate_dossier_path": _display_path(candidate_path) if candidate_path else None,
        "candidate_dossier_sha256": candidate_sha256,
        "report_sha256": sha256_file(report_path),
        "top_blockers": [
            "approved CMU eVTOL measurement-file download and immutable hashes",
            "audited experimental measurements with comparable cell boundaries",
            "published aviation-study reproduction",
            "candidate safety, cycle-life, cost, and manufacturability evidence",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "report_date": effective_date.isoformat(),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "python_version": sys.version,
        "config_hashes": config_hashes,
        "code_hashes": code_hashes,
        "code_snapshot_sha256": code_snapshot_sha256,
        "report_sha256": sha256_file(report_path),
        "summary_path": _display_path(summary_path),
        "summary_sha256": sha256_file(summary_path),
        "registry_counts": registries.summary(),
        "experimental_measurements": 0,
        "simulations_completed": len(mission_results),
        "simulation_campaign_rows": {
            "aviation_requirement_grid": simulation_summary[
                "aviation_requirement_grid_rows"
            ],
            "pack_trade_space": simulation_summary["pack_trade_space_rows"],
            "candidate_envelopes": simulation_summary["candidate_envelope_count"],
        },
        "simulation_campaign_sha256": simulation_sha256,
        "candidate_dossiers": candidate_summary["candidate_count"],
        "candidate_dossier_sha256": candidate_sha256,
        "dashboard_artifacts": len(dashboard_artifacts),
        "dashboard_manifest_sha256": sha256_file(dashboard_manifest_path),
        "ranking_enabled": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return report_path, manifest_path
