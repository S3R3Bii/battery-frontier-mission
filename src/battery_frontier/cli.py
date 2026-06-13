from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from battery_frontier.aviation.reference_cases import write_mission_results
from battery_frontier.candidates.dossiers import write_candidate_dossiers
from battery_frontier.data.connectors import (
    DEFAULT_SOURCE_QUERY,
    DEFAULT_SOURCE_ROWS,
    dry_run_source,
    source_status_rows,
    write_snapshot_manifest,
)
from battery_frontier.db import initialize_database
from battery_frontier.materials.campaign import write_materials_campaign
from battery_frontier.measurements.cmu_evtol import (
    download_cmu_evtol_files,
    verify_raw_snapshot,
    write_measurement_summary,
)
from battery_frontier.partners.dossiers import write_partner_dossiers
from battery_frontier.physics.reference_cases import write_reference_results
from battery_frontier.registry import load_registries
from battery_frontier.reporting.daily import generate_daily_report
from battery_frontier.reporting.method_cards import generate_dashboard_artifacts
from battery_frontier.simulations.campaign import write_simulation_campaign
from battery_frontier.website import export_website_data


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="battery-frontier")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate all Phase 0/1 registries")
    subparsers.add_parser("init-db", help="Create the local DuckDB schema")
    reference = subparsers.add_parser(
        "physics-reference",
        help="Calculate the Phase 2 reference fixtures",
    )
    reference.add_argument("--output", type=Path, help="Optional JSON output path")
    mission = subparsers.add_parser(
        "aviation-reference",
        help="Calculate the Phase 3 segmented mission fixtures",
    )
    mission.add_argument("--output", type=Path, help="Optional JSON output path")
    subparsers.add_parser(
        "dashboard-artifacts",
        help="Generate Phase 4 method cards and the dashboard artifact manifest",
    )
    candidates = subparsers.add_parser(
        "candidate-dossiers",
        help="Generate candidate evidence dossiers and metadata appendices",
    )
    candidates.add_argument("--output-dir", type=Path)
    candidates.add_argument("--mp-rows", type=int, default=2)
    candidates.add_argument(
        "--execute-materials-project",
        action="store_true",
        help="Fetch Materials Project metadata when MP_API_KEY is available",
    )
    candidates.add_argument(
        "--no-auto-materials-project",
        action="store_true",
        help="Do not auto-fetch Materials Project metadata even if MP_API_KEY exists",
    )
    report = subparsers.add_parser("daily-report", help="Generate Markdown and JSON reports")
    report.add_argument("--date", type=date.fromisoformat, help="Report date in YYYY-MM-DD")
    simulation = subparsers.add_parser(
        "simulation-campaign",
        help="Generate Phase 3.5/4.5 simulation campaign artifacts",
    )
    simulation.add_argument("--output-dir", type=Path)
    materials = subparsers.add_parser(
        "materials-campaign",
        help="Generate material hypothesis screening artifacts",
    )
    materials.add_argument("--output-dir", type=Path)
    subparsers.add_parser("source-status", help="Show connector and license readiness")
    dry_run = subparsers.add_parser(
        "source-dry-run",
        help="Build a source API request without publishing trusted data",
    )
    dry_run.add_argument("--source", required=True, help="Registry source id")
    dry_run.add_argument("--query", default=DEFAULT_SOURCE_QUERY)
    dry_run.add_argument("--rows", type=int, default=DEFAULT_SOURCE_ROWS)
    dry_run.add_argument("--execute", action="store_true", help="Optionally fetch metadata")
    dry_run.add_argument(
        "--write-manifest",
        action="store_true",
        help="Write an immutable source snapshot manifest",
    )
    dry_run.add_argument("--manifest-dir", type=Path)
    website = subparsers.add_parser(
        "website-data",
        help="Export static website mission-control data",
    )
    website.add_argument("--output", type=Path)
    fetch_cmu = subparsers.add_parser(
        "source-fetch-cmu-evtol",
        help="Create/fetch approved CMU eVTOL raw snapshot manifest",
    )
    fetch_cmu.add_argument(
        "--mode",
        choices=("metadata", "subset", "all"),
        default="metadata",
        help="metadata writes a manifest only; subset fetches README plus small CSV files",
    )
    fetch_cmu.add_argument("--raw-dir", type=Path)
    fetch_cmu.add_argument("--max-files", type=int)
    fetch_cmu.add_argument("--force", action="store_true")
    fetch_cmu.add_argument("--source-manifest", type=Path)
    fetch_cmu.add_argument("--output-dir", type=Path)
    verify_raw = subparsers.add_parser(
        "verify-raw-snapshots",
        help="Verify raw CMU eVTOL file hashes against the raw manifest",
    )
    verify_raw.add_argument("--manifest", type=Path)
    parse_cmu = subparsers.add_parser(
        "parse-cmu-evtol",
        help="Parse downloaded CMU eVTOL files and write a measurement summary",
    )
    parse_cmu.add_argument("--raw-manifest", type=Path)
    parse_cmu.add_argument("--output-dir", type=Path)
    parse_cmu.add_argument("--max-files", type=int, default=3)
    parse_cmu.add_argument("--max-rows-per-file", type=int, default=50_000)
    measurement = subparsers.add_parser(
        "measurement-summary",
        help="Generate the latest measurement summary artifact",
    )
    measurement.add_argument("--raw-manifest", type=Path)
    measurement.add_argument("--output-dir", type=Path)
    measurement.add_argument("--max-files", type=int, default=3)
    measurement.add_argument("--max-rows-per-file", type=int, default=50_000)
    partner = subparsers.add_parser(
        "partner-dossiers",
        help="Generate partner-facing latest and archived dossier reports",
    )
    partner.add_argument("--output-dir", type=Path)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "validate":
        registries = load_registries()
        for name, count in registries.summary().items():
            print(f"{name}: {count}")
        print("registry validation: passed")
    elif args.command == "init-db":
        path = initialize_database()
        print(f"database initialized: {path}")
    elif args.command == "physics-reference":
        registries = load_registries()
        path = write_reference_results(
            registries.physics_reference_cases,
            output_path=args.output,
        )
        print(f"reference results: {path}")
    elif args.command == "aviation-reference":
        registries = load_registries()
        path = write_mission_results(
            registries.segmented_mission_cases,
            output_path=args.output,
        )
        print(f"aviation results: {path}")
    elif args.command == "dashboard-artifacts":
        manifest_path, artifacts = generate_dashboard_artifacts()
        print(f"dashboard manifest: {manifest_path}")
        print(f"artifacts: {len(artifacts)}")
    elif args.command == "candidate-dossiers":
        execute_mp = args.execute_materials_project or (
            bool(os.environ.get("MP_API_KEY")) and not args.no_auto_materials_project
        )
        json_path, markdown_path, appendix_path = write_candidate_dossiers(
            output_dir=args.output_dir,
            execute_materials_project=execute_mp,
            mp_rows=args.mp_rows,
        )
        print(f"candidate dossiers: {json_path}")
        print(f"candidate report: {markdown_path}")
        print(f"materials project appendix: {appendix_path}")
    elif args.command == "daily-report":
        report_path, manifest_path = generate_daily_report(report_date=args.date)
        print(f"report: {report_path}")
        print(f"manifest: {manifest_path}")
    elif args.command == "simulation-campaign":
        summary_path, markdown_path, artifacts = write_simulation_campaign(
            output_dir=args.output_dir,
        )
        print(f"simulation summary: {summary_path}")
        print(f"simulation report: {markdown_path}")
        print(f"artifacts: {len(artifacts)}")
    elif args.command == "materials-campaign":
        summary_path, markdown_path, artifacts = write_materials_campaign(
            output_dir=args.output_dir,
        )
        print(f"materials summary: {summary_path}")
        print(f"materials report: {markdown_path}")
        print(f"artifacts: {len(artifacts)}")
    elif args.command == "source-status":
        registries = load_registries()
        print(json.dumps(source_status_rows(registries), indent=2, sort_keys=True))
    elif args.command == "source-dry-run":
        registries = load_registries()
        result = dry_run_source(
            registries,
            args.source,
            query=args.query,
            rows=args.rows,
            execute=args.execute,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.write_manifest:
            manifest_path = write_snapshot_manifest(
                result,
                output_dir=args.manifest_dir,
            )
            print(f"snapshot manifest: {manifest_path}")
    elif args.command == "website-data":
        path = export_website_data(output_path=args.output)
        print(f"website data: {path}")
    elif args.command == "source-fetch-cmu-evtol":
        path = download_cmu_evtol_files(
            mode=args.mode,
            raw_dir=args.raw_dir,
            max_files=args.max_files,
            force=args.force,
            source_manifest_path=args.source_manifest,
            output_dir=args.output_dir,
        )
        print(f"cmu raw manifest: {path}")
    elif args.command == "verify-raw-snapshots":
        rows = verify_raw_snapshot(args.manifest)
        print(json.dumps(rows, indent=2, sort_keys=True))
        failed = [
            row
            for row in rows
            if row["status"] != "metadata_only" and not row["hash_matches"]
        ]
        if failed:
            raise SystemExit(1)
    elif args.command in {"parse-cmu-evtol", "measurement-summary"}:
        json_path, markdown_path = write_measurement_summary(
            raw_manifest_path=args.raw_manifest,
            output_dir=args.output_dir,
            max_files=args.max_files,
            max_rows_per_file=args.max_rows_per_file,
        )
        print(f"measurement summary: {json_path}")
        print(f"measurement report: {markdown_path}")
    elif args.command == "partner-dossiers":
        manifest_path, archive_dir = write_partner_dossiers(output_dir=args.output_dir)
        print(f"partner dossier manifest: {manifest_path}")
        if archive_dir:
            print(f"partner dossier archive: {archive_dir}")
        else:
            print("partner dossier archive: not created (no significant input change)")


if __name__ == "__main__":
    main()
