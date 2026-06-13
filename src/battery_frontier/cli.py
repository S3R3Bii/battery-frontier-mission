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


if __name__ == "__main__":
    main()
