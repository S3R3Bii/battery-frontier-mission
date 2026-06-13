from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.aviation.segmented import (
    MissionDefinition,
    mission_definition_from_case,
    solve_battery_mass_closure,
)
from battery_frontier.candidates.dossiers import build_candidate_dossiers
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.provenance import sha256_file
from battery_frontier.registry import Registries, load_registries

DEFAULT_SIMULATION_DIR = PROJECT_ROOT / "reports" / "simulations"
RESEARCH_CELL_SPECIFIC_ENERGY_CEILING_WH_KG = 2500.0

AVIATION_ROUTE_FACTORS = (0.65, 1.0, 1.35)
AVIATION_PAYLOAD_FRACTIONS = (0.25, 0.6, 1.0)
AVIATION_PACK_SPECIFIC_ENERGIES_WH_KG = (300.0, 500.0, 700.0, 1000.0, 1500.0)
AVIATION_PROFILES = (
    {
        "profile": "conservative",
        "route_note": "higher reserve and degradation penalty",
        "reserve_duration_factor": 1.35,
        "lift_to_drag_factor": 0.9,
        "propulsion_efficiency_factor": 0.96,
        "thermal_availability": 0.88,
        "usable_depth_of_discharge": 0.72,
        "end_of_life_state_of_health": 0.78,
        "maximum_battery_mass_fraction": 0.36,
        "pack_specific_power_W_kg": 700.0,
        "maximum_continuous_c_rate": 1.5,
    },
    {
        "profile": "baseline",
        "route_note": "registered mission assumptions",
        "reserve_duration_factor": 1.0,
        "lift_to_drag_factor": 1.0,
        "propulsion_efficiency_factor": 1.0,
        "thermal_availability": 0.95,
        "usable_depth_of_discharge": 0.8,
        "end_of_life_state_of_health": 0.82,
        "maximum_battery_mass_fraction": 0.42,
        "pack_specific_power_W_kg": 900.0,
        "maximum_continuous_c_rate": 2.0,
    },
    {
        "profile": "optimistic",
        "route_note": "favorable aircraft and pack-operation assumptions",
        "reserve_duration_factor": 0.75,
        "lift_to_drag_factor": 1.12,
        "propulsion_efficiency_factor": 1.04,
        "thermal_availability": 0.98,
        "usable_depth_of_discharge": 0.88,
        "end_of_life_state_of_health": 0.9,
        "maximum_battery_mass_fraction": 0.5,
        "pack_specific_power_W_kg": 1300.0,
        "maximum_continuous_c_rate": 3.0,
    },
)

PACK_TARGETS_WH_KG = (500.0, 700.0, 1000.0, 1500.0)
PACK_CELL_TO_PACK_MASS_EFFICIENCIES = (0.55, 0.7, 0.85)
PACK_THERMAL_FRACTIONS = (0.05, 0.1, 0.18)
PACK_CONTAINMENT_FRACTIONS = (0.04, 0.08, 0.14)
PACK_CONTROL_FRACTIONS = (0.03, 0.06, 0.1)
PACK_RESERVE_MARGINS = (0.1, 0.2, 0.3)
PACK_DEGRADATION_MARGINS = (0.1, 0.2, 0.3)
PACK_USABLE_ENERGY_FRACTIONS = (0.7, 0.85, 0.95)

ENVELOPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "chemistry.lithium_ion_intercalation": {
        "basis": "what-if full-cell envelope from common intercalation-family ranges",
        "conservative_cell_Wh_kg": 180.0,
        "optimistic_cell_Wh_kg": 300.0,
        "projection_cell_Wh_kg": 350.0,
    },
    "chemistry.lithium_metal": {
        "basis": "what-if full-cell envelope requiring lithium inventory and safety audit",
        "conservative_cell_Wh_kg": 250.0,
        "optimistic_cell_Wh_kg": 500.0,
        "projection_cell_Wh_kg": 650.0,
    },
    "chemistry.solid_state_lithium": {
        "basis": "what-if solid-state full-cell envelope with pressure/interface unknowns",
        "conservative_cell_Wh_kg": 240.0,
        "optimistic_cell_Wh_kg": 500.0,
        "projection_cell_Wh_kg": 650.0,
    },
    "chemistry.lithium_sulfur": {
        "basis": "what-if full-cell envelope sensitive to electrolyte and lithium excess",
        "conservative_cell_Wh_kg": 260.0,
        "optimistic_cell_Wh_kg": 600.0,
        "projection_cell_Wh_kg": 900.0,
    },
    "chemistry.lithium_oxygen": {
        "basis": "what-if system envelope; oxygen management and reversibility unresolved",
        "conservative_cell_Wh_kg": 300.0,
        "optimistic_cell_Wh_kg": 800.0,
        "projection_cell_Wh_kg": 1500.0,
    },
    "chemistry.sodium_ion": {
        "basis": "what-if full-cell envelope for sodium-ion host systems",
        "conservative_cell_Wh_kg": 120.0,
        "optimistic_cell_Wh_kg": 220.0,
        "projection_cell_Wh_kg": 300.0,
    },
    "chemistry.multivalent": {
        "basis": "what-if envelope for magnesium, calcium, and aluminum systems",
        "conservative_cell_Wh_kg": 100.0,
        "optimistic_cell_Wh_kg": 300.0,
        "projection_cell_Wh_kg": 600.0,
    },
    "chemistry.zinc_air": {
        "basis": "what-if rechargeable zinc-air system envelope with air-system mass unknown",
        "conservative_cell_Wh_kg": 150.0,
        "optimistic_cell_Wh_kg": 500.0,
        "projection_cell_Wh_kg": 900.0,
    },
    "chemistry.structural_battery": {
        "basis": "what-if effective-system envelope; not separable from aircraft structure",
        "conservative_cell_Wh_kg": 50.0,
        "optimistic_cell_Wh_kg": 200.0,
        "projection_cell_Wh_kg": 400.0,
    },
    "chemistry.bio_derived_carbon_electrodes": {
        "basis": "electrode/scaffold lead only; no full rechargeable-cell energy envelope",
        "conservative_cell_Wh_kg": None,
        "optimistic_cell_Wh_kg": None,
        "projection_cell_Wh_kg": None,
    },
}


def validate_sweep_parameters(**parameters: float) -> None:
    positive_fields = {
        "route_distance_km",
        "aircraft_mass_kg",
        "pack_specific_energy_Wh_kg",
        "pack_specific_power_W_kg",
        "maximum_continuous_c_rate",
        "reserve_duration_min",
        "voltage_V",
    }
    unit_interval_fields = {
        "propulsion_efficiency",
        "usable_depth_of_discharge",
        "end_of_life_state_of_health",
        "thermal_availability",
        "cell_to_pack_mass_efficiency",
        "usable_energy_fraction",
    }
    open_unit_interval_fields = {
        "battery_mass_fraction",
        "maximum_battery_mass_fraction",
        "reserve_margin_fraction",
        "degradation_margin_fraction",
    }
    nonnegative_fields = {
        "payload_mass_kg",
        "thermal_mass_fraction",
        "containment_mass_fraction",
        "controls_mass_fraction",
    }
    for name, value in parameters.items():
        if name in positive_fields and value <= 0:
            raise ValueError(f"{name} must be positive")
        if name in unit_interval_fields and not 0 < value <= 1:
            raise ValueError(f"{name} must be in (0, 1]")
        if name in open_unit_interval_fields and not 0 < value < 1:
            raise ValueError(f"{name} must be in (0, 1)")
        if name in nonnegative_fields and value < 0:
            raise ValueError(f"{name} cannot be negative")


def _safe_solve(definition: MissionDefinition) -> Any:
    try:
        return solve_battery_mass_closure(definition)
    except ValueError as exc:
        return {
            "feasible": False,
            "converged": False,
            "battery_mass_kg": None,
            "battery_mass_fraction": None,
            "takeoff_mass_kg": None,
            "nominal_battery_energy_Wh": None,
            "peak_electrical_power_W": None,
            "limiting_constraint": "invalid_input",
            "reasons": (str(exc),),
        }


def _solution_value(solution: Any, attribute: str) -> Any:
    if isinstance(solution, dict):
        return solution.get(attribute)
    return getattr(solution, attribute)


def _solution_reasons(solution: Any) -> tuple[str, ...]:
    reasons = _solution_value(solution, "reasons")
    return tuple(reasons or ())


def _with_profile(
    definition: MissionDefinition,
    *,
    route_factor: float,
    payload_fraction: float,
    pack_specific_energy_Wh_kg: float,
    profile: dict[str, Any],
) -> MissionDefinition:
    route_distance_km = definition.route_distance_km * route_factor
    payload_mass_kg = definition.maximum_payload_kg * payload_fraction
    lift_factor = float(profile["lift_to_drag_factor"])
    propulsion_efficiency = min(
        definition.propulsion_efficiency * float(profile["propulsion_efficiency_factor"]),
        0.99,
    )
    validate_sweep_parameters(
        route_distance_km=route_distance_km,
        payload_mass_kg=payload_mass_kg,
        pack_specific_energy_Wh_kg=pack_specific_energy_Wh_kg,
        pack_specific_power_W_kg=float(profile["pack_specific_power_W_kg"]),
        maximum_continuous_c_rate=float(profile["maximum_continuous_c_rate"]),
        reserve_duration_min=definition.reserve_loiter_duration_min
        * float(profile["reserve_duration_factor"]),
        propulsion_efficiency=propulsion_efficiency,
        usable_depth_of_discharge=float(profile["usable_depth_of_discharge"]),
        end_of_life_state_of_health=float(profile["end_of_life_state_of_health"]),
        thermal_availability=float(profile["thermal_availability"]),
        maximum_battery_mass_fraction=float(profile["maximum_battery_mass_fraction"]),
    )
    return replace(
        definition,
        route_distance_km=route_distance_km,
        range_search_upper_km=max(definition.range_search_upper_km, route_distance_km * 1.2),
        payload_mass_kg=payload_mass_kg,
        reserve_loiter_duration_min=(
            definition.reserve_loiter_duration_min
            * float(profile["reserve_duration_factor"])
        ),
        cruise_lift_to_drag_ratio=definition.cruise_lift_to_drag_ratio * lift_factor,
        climb_lift_to_drag_ratio=definition.climb_lift_to_drag_ratio * lift_factor,
        descent_lift_to_drag_ratio=definition.descent_lift_to_drag_ratio * lift_factor,
        reserve_lift_to_drag_ratio=definition.reserve_lift_to_drag_ratio * lift_factor,
        propulsion_efficiency=propulsion_efficiency,
        thermal_availability=float(profile["thermal_availability"]),
        usable_depth_of_discharge=float(profile["usable_depth_of_discharge"]),
        end_of_life_state_of_health=float(profile["end_of_life_state_of_health"]),
        maximum_battery_mass_fraction=float(profile["maximum_battery_mass_fraction"]),
        pack_specific_energy_Wh_kg=pack_specific_energy_Wh_kg,
        pack_specific_power_W_kg=float(profile["pack_specific_power_W_kg"]),
        maximum_continuous_c_rate=float(profile["maximum_continuous_c_rate"]),
    )


def _required_pack_energy(
    definition: MissionDefinition,
    *,
    lower_Wh_kg: float = 200.0,
    upper_Wh_kg: float = 3000.0,
    iterations: int = 22,
) -> tuple[float | None, tuple[str, ...]]:
    upper_solution = _safe_solve(replace(definition, pack_specific_energy_Wh_kg=upper_Wh_kg))
    if not _solution_value(upper_solution, "feasible"):
        return None, _solution_reasons(upper_solution)

    lower_solution = _safe_solve(replace(definition, pack_specific_energy_Wh_kg=lower_Wh_kg))
    if _solution_value(lower_solution, "feasible"):
        return lower_Wh_kg, ()

    low = lower_Wh_kg
    high = upper_Wh_kg
    for _ in range(iterations):
        midpoint = (low + high) / 2.0
        solution = _safe_solve(replace(definition, pack_specific_energy_Wh_kg=midpoint))
        if _solution_value(solution, "feasible"):
            high = midpoint
        else:
            low = midpoint
    return round(high, 3), ()


def build_aviation_requirement_grid(registries: Registries) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in registries.segmented_mission_cases:
        base = mission_definition_from_case(case)
        for route_factor in AVIATION_ROUTE_FACTORS:
            for payload_fraction in AVIATION_PAYLOAD_FRACTIONS:
                for profile in AVIATION_PROFILES:
                    requirement_definition = _with_profile(
                        base,
                        route_factor=route_factor,
                        payload_fraction=payload_fraction,
                        pack_specific_energy_Wh_kg=700.0,
                        profile=profile,
                    )
                    required_energy, requirement_reasons = _required_pack_energy(
                        requirement_definition
                    )
                    for pack_energy in AVIATION_PACK_SPECIFIC_ENERGIES_WH_KG:
                        definition = replace(
                            requirement_definition,
                            pack_specific_energy_Wh_kg=pack_energy,
                        )
                        solution = _safe_solve(definition)
                        feasible = bool(_solution_value(solution, "feasible"))
                        reasons = _solution_reasons(solution)
                        row = {
                            "artifact_type": "aviation_requirement_grid_row",
                            "evidence_class": "simulation_estimate",
                            "performance_evidence": False,
                            "audited_measurement": False,
                            "ranking_evidence": False,
                            "base_case_id": case.id,
                            "base_case_name": case.name,
                            "profile": profile["profile"],
                            "profile_note": profile["route_note"],
                            "route_factor": route_factor,
                            "route_distance_km": round(definition.route_distance_km, 3),
                            "payload_fraction": payload_fraction,
                            "payload_mass_kg": round(definition.payload_mass_kg, 3),
                            "reserve_duration_min": round(
                                definition.reserve_loiter_duration_min,
                                3,
                            ),
                            "cruise_lift_to_drag_ratio": round(
                                definition.cruise_lift_to_drag_ratio,
                                3,
                            ),
                            "propulsion_efficiency": round(
                                definition.propulsion_efficiency,
                                5,
                            ),
                            "thermal_availability": definition.thermal_availability,
                            "usable_depth_of_discharge": (
                                definition.usable_depth_of_discharge
                            ),
                            "end_of_life_state_of_health": (
                                definition.end_of_life_state_of_health
                            ),
                            "maximum_battery_mass_fraction": (
                                definition.maximum_battery_mass_fraction
                            ),
                            "pack_specific_energy_Wh_kg": pack_energy,
                            "pack_specific_power_W_kg": (
                                definition.pack_specific_power_W_kg
                            ),
                            "maximum_continuous_c_rate": (
                                definition.maximum_continuous_c_rate
                            ),
                            "required_pack_specific_energy_Wh_kg": required_energy,
                            "required_energy_status": (
                                "bounded" if required_energy is not None else "above_search_bound"
                            ),
                            "feasible": feasible,
                            "converged": bool(_solution_value(solution, "converged")),
                            "limiting_constraint": _solution_value(
                                solution,
                                "limiting_constraint",
                            ),
                            "battery_mass_kg": _solution_value(solution, "battery_mass_kg"),
                            "battery_mass_fraction": _solution_value(
                                solution,
                                "battery_mass_fraction",
                            ),
                            "takeoff_mass_kg": _solution_value(solution, "takeoff_mass_kg"),
                            "nominal_battery_energy_Wh": _solution_value(
                                solution,
                                "nominal_battery_energy_Wh",
                            ),
                            "peak_electrical_power_W": _solution_value(
                                solution,
                                "peak_electrical_power_W",
                            ),
                            "infeasibility_reasons": "; ".join(
                                reasons or requirement_reasons
                            ),
                        }
                        rows.append(row)
    return rows


def build_pack_trade_space() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in PACK_TARGETS_WH_KG:
        for cell_to_pack in PACK_CELL_TO_PACK_MASS_EFFICIENCIES:
            for thermal_fraction in PACK_THERMAL_FRACTIONS:
                for containment_fraction in PACK_CONTAINMENT_FRACTIONS:
                    for controls_fraction in PACK_CONTROL_FRACTIONS:
                        for reserve_margin in PACK_RESERVE_MARGINS:
                            for degradation_margin in PACK_DEGRADATION_MARGINS:
                                for usable_fraction in PACK_USABLE_ENERGY_FRACTIONS:
                                    validate_sweep_parameters(
                                        pack_specific_energy_Wh_kg=target,
                                        cell_to_pack_mass_efficiency=cell_to_pack,
                                        thermal_mass_fraction=thermal_fraction,
                                        containment_mass_fraction=containment_fraction,
                                        controls_mass_fraction=controls_fraction,
                                        reserve_margin_fraction=reserve_margin,
                                        degradation_margin_fraction=degradation_margin,
                                        usable_energy_fraction=usable_fraction,
                                    )
                                    overhead_multiplier = (
                                        1
                                        + thermal_fraction
                                        + containment_fraction
                                        + controls_fraction
                                    )
                                    effective_fraction = (
                                        cell_to_pack
                                        * usable_fraction
                                        * (1 - reserve_margin)
                                        * (1 - degradation_margin)
                                        / overhead_multiplier
                                    )
                                    required_cell_energy = (
                                        target / effective_fraction
                                        if effective_fraction > 0
                                        else None
                                    )
                                    infeasible = (
                                        required_cell_energy is None
                                        or required_cell_energy
                                        > RESEARCH_CELL_SPECIFIC_ENERGY_CEILING_WH_KG
                                    )
                                    rows.append(
                                        {
                                            "artifact_type": "pack_trade_space_row",
                                            "evidence_class": "simulation_estimate",
                                            "performance_evidence": False,
                                            "audited_measurement": False,
                                            "ranking_evidence": False,
                                            "target_pack_specific_energy_Wh_kg": target,
                                            "cell_to_pack_mass_efficiency": cell_to_pack,
                                            "thermal_mass_fraction": thermal_fraction,
                                            "containment_mass_fraction": (
                                                containment_fraction
                                            ),
                                            "controls_mass_fraction": controls_fraction,
                                            "reserve_margin_fraction": reserve_margin,
                                            "degradation_margin_fraction": (
                                                degradation_margin
                                            ),
                                            "usable_energy_fraction": usable_fraction,
                                            "effective_pack_fraction": round(
                                                effective_fraction,
                                                6,
                                            ),
                                            "required_cell_specific_energy_Wh_kg": (
                                                round(required_cell_energy, 3)
                                                if required_cell_energy is not None
                                                else None
                                            ),
                                            "infeasible": infeasible,
                                            "infeasibility_reason": (
                                                "required cell energy exceeds research ceiling"
                                                if infeasible
                                                else ""
                                            ),
                                        }
                                    )
    return rows


def _pack_sensitivity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variables = [
        "cell_to_pack_mass_efficiency",
        "thermal_mass_fraction",
        "containment_mass_fraction",
        "controls_mass_fraction",
        "reserve_margin_fraction",
        "degradation_margin_fraction",
        "usable_energy_fraction",
    ]
    sensitivity = []
    for variable in variables:
        grouped: dict[float, list[float]] = defaultdict(list)
        for row in rows:
            value = row["required_cell_specific_energy_Wh_kg"]
            if value is not None:
                grouped[float(row[variable])].append(float(value))
        means = {
            level: sum(values) / len(values)
            for level, values in grouped.items()
            if values
        }
        if not means:
            continue
        sensitivity.append(
            {
                "variable": variable,
                "mean_required_cell_energy_spread_Wh_kg": round(
                    max(means.values()) - min(means.values()),
                    3,
                ),
                "lowest_mean_level": min(means, key=means.get),
                "highest_mean_level": max(means, key=means.get),
                "interpretation": (
                    "Architecture sensitivity only; this is not a material ranking."
                ),
            }
        )
    return sorted(
        sensitivity,
        key=lambda item: item["mean_required_cell_energy_spread_Wh_kg"],
        reverse=True,
    )


def _envelope_modes(defaults: dict[str, Any], *, hemp: bool) -> list[dict[str, Any]]:
    modes = [
        ("conservative", defaults["conservative_cell_Wh_kg"]),
        ("optimistic", defaults["optimistic_cell_Wh_kg"]),
        ("theoretical_projection", defaults["projection_cell_Wh_kg"]),
        ("unknown", None),
    ]
    output = []
    for mode, value in modes:
        output.append(
            {
                "mode": mode,
                "full_cell_specific_energy_Wh_kg": value,
                "usable_for_ranking": False,
                "performance_evidence": False,
                "audited_measurement": False,
                "system_boundary": (
                    "speculative carbon electrode/scaffold lead only"
                    if hemp
                    else "simulation envelope for full-cell or system what-if study"
                ),
                "note": (
                    "Hemp-derived graphitic carbon is not mapped to battery-cell energy; "
                    "supercapacitor behavior is not aviation battery evidence."
                    if hemp
                    else "Parameter envelope only; requires audited full-cell evidence."
                ),
            }
        )
    return output


def build_candidate_envelopes(
    registries: Registries,
    candidate_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    payload = candidate_payload or build_candidate_dossiers(
        registries,
        execute_materials_project=False,
    )
    rows = []
    for candidate in payload["dossiers"]:
        chemistry_id = candidate["chemistry_family_id"]
        defaults = ENVELOPE_DEFAULTS.get(
            chemistry_id,
            {
                "basis": "unknown candidate family; no numerical what-if envelope",
                "conservative_cell_Wh_kg": None,
                "optimistic_cell_Wh_kg": None,
                "projection_cell_Wh_kg": None,
            },
        )
        hemp = candidate["id"] == "candidate.hemp_bast_graphitic_carbon"
        rows.append(
            {
                "artifact_type": "candidate_envelope",
                "candidate_id": candidate["id"],
                "display_name": candidate["display_name"],
                "chemistry_family_id": chemistry_id,
                "chemistry_family": candidate["chemistry_family"],
                "evidence_class": "simulation_estimate_parameter_envelope",
                "basis": defaults["basis"],
                "ranking_allowed": False,
                "ranking_evidence": False,
                "performance_evidence": False,
                "audited_measurement_count": 0,
                "hemp_specific_guardrail": (
                    "Speculative carbon electrode/scaffold only; not validated graphene "
                    "and not aviation-grade battery evidence."
                    if hemp
                    else ""
                ),
                "envelopes": _envelope_modes(defaults, hemp=hemp),
            }
        )
    return rows


def _infeasible_ledger(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    infeasible = [row for row in rows if not row["feasible"]]
    infeasible.sort(
        key=lambda row: (
            row["base_case_id"],
            row["profile"],
            -float(row["route_distance_km"]),
            -float(row["payload_mass_kg"]),
            float(row["pack_specific_energy_Wh_kg"]),
        )
    )
    return [
        {
            "base_case_id": row["base_case_id"],
            "profile": row["profile"],
            "route_distance_km": row["route_distance_km"],
            "payload_mass_kg": row["payload_mass_kg"],
            "pack_specific_energy_Wh_kg": row["pack_specific_energy_Wh_kg"],
            "limiting_constraint": row["limiting_constraint"],
            "reasons": row["infeasibility_reasons"],
        }
        for row in infeasible[:limit]
    ]


def _counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _summary(
    aviation_rows: list[dict[str, Any]],
    pack_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    feasible_count = sum(bool(row["feasible"]) for row in aviation_rows)
    infeasible_count = len(aviation_rows) - feasible_count
    bounded_requirements = [
        float(row["required_pack_specific_energy_Wh_kg"])
        for row in aviation_rows
        if row["required_pack_specific_energy_Wh_kg"] is not None
    ]
    pack_infeasible_count = sum(bool(row["infeasible"]) for row in pack_rows)
    max_required = max(bounded_requirements, default=None)
    median_required = None
    if bounded_requirements:
        ordered = sorted(bounded_requirements)
        median_required = ordered[len(ordered) // 2]
    return {
        "phase": "3.5/4.5",
        "phase_status": "simulation campaign active; validation still pending",
        "artifact_type": "simulation_campaign_summary",
        "campaign_status": "generated",
        "simulation_only": True,
        "technology_readiness_claim": False,
        "performance_evidence": False,
        "ranking_enabled": False,
        "audited_measurements": 0,
        "aviation_requirement_grid_rows": len(aviation_rows),
        "aviation_feasible_count": feasible_count,
        "aviation_infeasible_count": infeasible_count,
        "aviation_limiting_constraints": _counter_dict(
            [row["limiting_constraint"] for row in aviation_rows]
        ),
        "bounded_requirement_count": len(bounded_requirements),
        "max_required_pack_specific_energy_Wh_kg": max_required,
        "median_required_pack_specific_energy_Wh_kg": median_required,
        "pack_trade_space_rows": len(pack_rows),
        "pack_trade_infeasible_count": pack_infeasible_count,
        "candidate_envelope_count": len(candidate_rows),
        "hemp_candidate_present": any(
            row["candidate_id"] == "candidate.hemp_bast_graphitic_carbon"
            for row in candidate_rows
        ),
        "pack_sensitivity": _pack_sensitivity(pack_rows),
        "infeasible_region_ledger": _infeasible_ledger(aviation_rows),
        "what_would_need_to_be_true": [
            "Audited full-cell measurements need comparable system boundaries and uncertainty.",
            "Pack overhead, containment, thermal control, reserve, and degradation "
            "margins need explicit mass accounting.",
            "Mission feasibility needs published aircraft-study validation and "
            "transient power checks.",
            "Candidate material envelopes need cycle-life, safety, manufacturing, "
            "and source-lineage evidence before ranking.",
            "Hemp-derived graphitic carbon needs primary-paper audit and full-cell "
            "translation before any aviation claim.",
        ],
    }


def build_simulation_campaign(
    registries: Registries | None = None,
    *,
    candidate_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_registries = registries or load_registries()
    aviation_rows = build_aviation_requirement_grid(active_registries)
    pack_rows = build_pack_trade_space()
    candidate_rows = build_candidate_envelopes(active_registries, candidate_payload)
    summary = _summary(aviation_rows, pack_rows, candidate_rows)
    return {
        "artifact_type": "simulation_campaign",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "claim_boundary": (
            "Deterministic parameter sweeps and what-if envelopes only. These outputs "
            "are not experimental validation, candidate rankings, aircraft designs, "
            "or certification evidence."
        ),
        "summary": summary,
        "aviation_requirement_grid": aviation_rows,
        "pack_trade_space": pack_rows,
        "candidate_envelopes": candidate_rows,
        "limitations": [
            "No row is an audited battery measurement.",
            "No candidate envelope enables chemistry ranking.",
            "Feasible simulation rows only satisfy configured assumptions.",
            "Materials metadata and fixtures remain non-performance evidence.",
        ],
    }


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _artifact_record(path: Path, row_count: int | None = None) -> dict[str, Any]:
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "sha256": sha256_file(path),
        "row_count": row_count,
    }


def _write_markdown_summary(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Simulation Campaign Summary",
        "",
        "> Parameter sweeps and what-if envelopes only. Not experimental validation,",
        "> chemistry ranking, aircraft design, or certification evidence.",
        "",
        "## Status",
        "",
        f"- Phase lane: {summary['phase']}",
        f"- Aviation grid rows: {summary['aviation_requirement_grid_rows']}",
        f"- Feasible aviation rows: {summary['aviation_feasible_count']}",
        f"- Infeasible aviation rows: {summary['aviation_infeasible_count']}",
        f"- Pack trade rows: {summary['pack_trade_space_rows']}",
        f"- Pack trade rows above research ceiling: {summary['pack_trade_infeasible_count']}",
        f"- Candidate envelopes: {summary['candidate_envelope_count']}",
        f"- Audited measurements: {summary['audited_measurements']}",
        f"- Ranking enabled: {summary['ranking_enabled']}",
        "",
        "## Limiting Constraints",
        "",
        "```json",
        json.dumps(summary["aviation_limiting_constraints"], indent=2, sort_keys=True),
        "```",
        "",
        "## What Would Need To Be True",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["what_would_need_to_be_true"])
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Simulation rows cannot appear as audited measurements.",
            "- Candidate envelopes cannot enable ranking.",
            "- Hemp-derived graphitic carbon remains speculative electrode/scaffold context.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_simulation_campaign(
    *,
    output_dir: Path | None = None,
) -> tuple[Path, Path, dict[str, Path]]:
    destination = output_dir or DEFAULT_SIMULATION_DIR
    destination.mkdir(parents=True, exist_ok=True)
    payload = build_simulation_campaign()

    aviation_json = destination / "aviation_requirement_grid.json"
    aviation_csv = destination / "aviation_requirement_grid.csv"
    pack_json = destination / "pack_trade_space.json"
    pack_csv = destination / "pack_trade_space.csv"
    envelopes_json = destination / "candidate_envelopes.json"
    summary_path = destination / "simulation_campaign_summary.json"
    markdown_path = destination / "simulation_campaign_summary.md"

    _write_json(
        aviation_json,
        {
            "artifact_type": "aviation_requirement_grid",
            "row_count": len(payload["aviation_requirement_grid"]),
            "rows": payload["aviation_requirement_grid"],
        },
    )
    _write_csv(aviation_csv, payload["aviation_requirement_grid"])
    _write_json(
        pack_json,
        {
            "artifact_type": "pack_trade_space",
            "row_count": len(payload["pack_trade_space"]),
            "rows": payload["pack_trade_space"],
        },
    )
    _write_csv(pack_csv, payload["pack_trade_space"])
    _write_json(
        envelopes_json,
        {
            "artifact_type": "candidate_envelopes",
            "row_count": len(payload["candidate_envelopes"]),
            "rows": payload["candidate_envelopes"],
        },
    )

    artifacts = {
        "aviation_requirement_grid_json": _artifact_record(
            aviation_json,
            len(payload["aviation_requirement_grid"]),
        ),
        "aviation_requirement_grid_csv": _artifact_record(
            aviation_csv,
            len(payload["aviation_requirement_grid"]),
        ),
        "pack_trade_space_json": _artifact_record(pack_json, len(payload["pack_trade_space"])),
        "pack_trade_space_csv": _artifact_record(pack_csv, len(payload["pack_trade_space"])),
        "candidate_envelopes_json": _artifact_record(
            envelopes_json,
            len(payload["candidate_envelopes"]),
        ),
    }
    summary_payload = {
        **payload,
        "artifacts": artifacts,
        "payload_sha256": hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest(),
    }
    _write_json(summary_path, summary_payload)
    _write_markdown_summary(summary_payload, markdown_path)
    return (
        summary_path,
        markdown_path,
        {
            "aviation_json": aviation_json,
            "aviation_csv": aviation_csv,
            "pack_json": pack_json,
            "pack_csv": pack_csv,
            "candidate_envelopes_json": envelopes_json,
        },
    )


def verify_simulation_artifacts(summary_path: Path | None = None) -> list[dict[str, Any]]:
    path = summary_path or DEFAULT_SIMULATION_DIR / "simulation_campaign_summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for artifact_id, artifact in payload["artifacts"].items():
        artifact_path = PROJECT_ROOT / artifact["path"]
        exists = artifact_path.exists()
        current_hash = sha256_file(artifact_path) if exists else None
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": artifact["path"],
                "exists": exists,
                "hash_matches": exists and current_hash == artifact["sha256"],
                "expected_sha256": artifact["sha256"],
                "current_sha256": current_hash,
                "row_count": artifact["row_count"],
            }
        )
    return rows
