from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.aviation.segmented import (
    MissionSolution,
    mission_definition_from_case,
    mission_sensitivity,
    payload_range_curve,
    solve_battery_mass_closure,
)
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.provenance import hash_files, sha256_file
from battery_frontier.schemas import SegmentedMissionCase


def _solution_payload(
    case: SegmentedMissionCase,
    solution: MissionSolution,
) -> dict[str, Any]:
    return {
        "id": case.id,
        "name": case.name,
        "status": case.status,
        "evidence_class": "simulation_estimate using speculative mission inputs",
        "description": case.description,
        "converged": solution.converged,
        "feasible": solution.feasible,
        "reasons": list(solution.reasons),
        "iterations": solution.iterations,
        "configured_pack_specific_energy_Wh_kg": case.pack_specific_energy_Wh_kg,
        "configured_pack_specific_power_W_kg": case.pack_specific_power_W_kg,
        "configured_maximum_battery_mass_fraction": case.maximum_battery_mass_fraction,
        "route_distance_km": case.route_distance_km,
        "maximum_takeoff_mass_kg": case.maximum_takeoff_mass_kg,
        "payload_mass_kg": case.payload_mass_kg,
        "battery_mass_kg": solution.battery_mass_kg,
        "battery_mass_interpretation": (
            "converged sizing result"
            if solution.converged
            else "last solver iterate; not a converged sizing result"
        ),
        "takeoff_mass_kg": solution.takeoff_mass_kg,
        "battery_mass_fraction": solution.battery_mass_fraction,
        "terminal_electrical_energy_Wh": solution.terminal_electrical_energy_Wh,
        "nominal_battery_energy_Wh": solution.nominal_battery_energy_Wh,
        "peak_electrical_power_W": solution.peak_electrical_power_W,
        "energy_limited_mass_kg": solution.energy_limited_mass_kg,
        "specific_power_limited_mass_kg": solution.specific_power_limited_mass_kg,
        "c_rate_limited_mass_kg": solution.c_rate_limited_mass_kg,
        "limiting_constraint": solution.limiting_constraint,
        "segments": [
            {
                "name": segment.name,
                "kind": segment.kind.value,
                "duration_min": segment.duration_min,
                "horizontal_distance_km": segment.horizontal_distance_km,
                "mechanical_energy_Wh": segment.mechanical_energy_Wh,
                "electrical_energy_Wh": segment.electrical_energy_Wh,
                "average_electrical_power_W": segment.average_electrical_power_W,
                "assumptions": segment.assumptions,
            }
            for segment in solution.segments
        ],
        "payload_range_curve": payload_range_curve(solution.definition),
        "sensitivity": mission_sensitivity(solution.definition),
        "uncertainty_note": case.uncertainty_note,
        "citation_ids": case.citation_ids,
    }


def calculate_mission_case(case: SegmentedMissionCase) -> dict[str, Any]:
    definition = mission_definition_from_case(case)
    return _solution_payload(case, solve_battery_mass_closure(definition))


def calculate_all_mission_cases(
    cases: list[SegmentedMissionCase],
) -> list[dict[str, Any]]:
    return [calculate_mission_case(case) for case in cases]


def write_mission_results(
    cases: list[SegmentedMissionCase],
    output_path: Path | None = None,
) -> Path:
    destination = (
        output_path
        or PROJECT_ROOT / "reports" / "aviation" / "phase3_mission_cases.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    config_path = PROJECT_ROOT / "configs" / "segmented_mission_cases.yaml"
    code_paths = [
        *PROJECT_ROOT.glob("src/battery_frontier/aviation/*.py"),
        PROJECT_ROOT / "src" / "battery_frontier" / "schemas.py",
    ]
    code_hashes = hash_files(code_paths, PROJECT_ROOT)
    code_snapshot_sha256 = hashlib.sha256(
        json.dumps(code_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()
    payload = {
        "phase": "3",
        "claim_status": "simulation estimates from speculative design-study inputs",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "config_sha256": sha256_file(config_path),
        "code_hashes": code_hashes,
        "code_snapshot_sha256": code_snapshot_sha256,
        "cases": calculate_all_mission_cases(cases),
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination
