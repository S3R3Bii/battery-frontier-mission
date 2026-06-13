from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.physics.bom import (
    CellBillOfMaterials,
    CellComponent,
    PackBillOfMaterials,
    PackComponent,
)
from battery_frontier.physics.stoichiometry import (
    ElectrochemicalReaction,
    ReactionSide,
    ReactionSpecies,
)
from battery_frontier.physics.system_metrics import (
    gravimetric_to_volumetric_energy_Wh_l,
)
from battery_frontier.physics.uncertainty import (
    PositiveInterval,
    product_interval,
    theoretical_capacity_interval_mAh_g,
)
from battery_frontier.physics.voltage import VoltageProfile, VoltageSegment
from battery_frontier.provenance import hash_files, sha256_file
from battery_frontier.schemas import PhysicsReferenceCase


def _reaction(case: PhysicsReferenceCase) -> ElectrochemicalReaction:
    reaction = ElectrochemicalReaction(
        electrons_transferred=case.electrons_transferred,
        species=tuple(
            ReactionSpecies(
                name=item.name,
                formula=item.formula,
                side=ReactionSide(item.side.value),
                stoichiometric_coefficient=item.stoichiometric_coefficient,
                molar_mass_g_mol=item.molar_mass_g_mol,
                included_in_mass_basis=item.included_in_mass_basis,
            )
            for item in case.species
        ),
        mass_basis_description=case.mass_basis_description,
    )
    reaction.validate_mass_balance(case.mass_balance_tolerance_fraction)
    return reaction


def calculate_reference_case(case: PhysicsReferenceCase) -> dict[str, Any]:
    reaction = _reaction(case)
    capacity = reaction.theoretical_specific_capacity_mAh_g
    result: dict[str, Any] = {
        "id": case.id,
        "name": case.name,
        "status": case.status,
        "evidence_class": case.evidence_class.value,
        "description": case.description,
        "reaction_equation": reaction.equation,
        "mass_basis_description": reaction.mass_basis_description,
        "reaction_mass_basis_g_mol": reaction.mass_basis_molar_mass_g_mol,
        "mass_balance_relative_error": reaction.mass_balance_relative_error,
        "theoretical_specific_capacity_mAh_g": capacity,
        "theoretical_specific_capacity_evidence_class": "theoretical_limit",
        "uncertainty_note": case.uncertainty_note,
        "citation_ids": case.citation_ids,
    }

    if case.reaction_molar_mass_range is not None:
        capacity_interval = theoretical_capacity_interval_mAh_g(
            PositiveInterval(
                nominal=case.electrons_transferred,
                lower=case.electrons_transferred,
                upper=case.electrons_transferred,
                unit="mol e-/reaction",
            ),
            PositiveInterval(**case.reaction_molar_mass_range.model_dump()),
        )
        result["capacity_interval_mAh_g"] = {
            "nominal": capacity_interval.nominal,
            "lower": capacity_interval.lower,
            "upper": capacity_interval.upper,
        }

    if case.voltage_profile:
        profile = VoltageProfile(
            tuple(
                VoltageSegment(
                    label=item.label,
                    capacity_fraction=item.capacity_fraction,
                    average_voltage_v=item.average_voltage_v,
                )
                for item in case.voltage_profile
            )
        )
        active_specific_energy = profile.specific_energy_Wh_kg(capacity)
        result["average_voltage_v"] = profile.average_voltage_v
        result["active_specific_energy_Wh_kg"] = active_specific_energy
        result["active_specific_energy_evidence_class"] = (
            "simulation_estimate using declared voltage-profile inputs"
        )

        if case.average_voltage_range is not None and case.reaction_molar_mass_range:
            capacity_range = result["capacity_interval_mAh_g"]
            energy_interval = product_interval(
                PositiveInterval(
                    nominal=capacity_range["nominal"],
                    lower=capacity_range["lower"],
                    upper=capacity_range["upper"],
                    unit="mAh/g",
                ),
                PositiveInterval(**case.average_voltage_range.model_dump()),
                unit="Wh/kg",
            )
            result["active_specific_energy_interval_Wh_kg"] = {
                "nominal": energy_interval.nominal,
                "lower": energy_interval.lower,
                "upper": energy_interval.upper,
            }

        if (
            case.active_material_density_kg_l is not None
            and case.electrode_packing_fraction is not None
        ):
            result["packed_active_volumetric_energy_Wh_l"] = (
                gravimetric_to_volumetric_energy_Wh_l(
                    active_specific_energy,
                    case.active_material_density_kg_l,
                    case.electrode_packing_fraction,
                )
            )

        if case.cell_design is not None:
            cell = CellBillOfMaterials(
                components=tuple(
                    CellComponent(**component.model_dump())
                    for component in case.cell_design.components
                ),
                active_specific_energy_Wh_kg=active_specific_energy,
                capacity_utilization=case.cell_design.capacity_utilization,
                voltage_efficiency=case.cell_design.voltage_efficiency,
                discharge_efficiency=case.cell_design.discharge_efficiency,
            )
            result["cell"] = {
                "evidence_class": "simulation_estimate using illustrative inputs",
                "total_mass_g": cell.total_mass_g,
                "active_reactant_mass_g": cell.active_reactant_mass_g,
                "active_mass_fraction": cell.active_mass_fraction,
                "nominal_energy_Wh": cell.nominal_energy_Wh,
                "specific_energy_Wh_kg": cell.specific_energy_Wh_kg,
                "total_volume_l": cell.total_volume_l,
                "volumetric_energy_Wh_l": cell.volumetric_energy_Wh_l,
                "mass_fractions": cell.mass_fractions,
            }

            if case.pack_design is not None:
                pack = PackBillOfMaterials(
                    components=tuple(
                        PackComponent(**component.model_dump())
                        for component in case.pack_design.components
                    ),
                    cell_specific_energy_Wh_kg=cell.specific_energy_Wh_kg,
                    discharge_efficiency=case.pack_design.discharge_efficiency,
                )
                result["pack"] = {
                    "evidence_class": "simulation_estimate using illustrative inputs",
                    "total_mass_kg": pack.total_mass_kg,
                    "cell_mass_kg": pack.cell_mass_kg,
                    "cell_mass_fraction": pack.cell_mass_fraction,
                    "nominal_energy_Wh": pack.nominal_energy_Wh,
                    "specific_energy_Wh_kg": pack.specific_energy_Wh_kg,
                    "total_volume_l": pack.total_volume_l,
                    "volumetric_energy_Wh_l": pack.volumetric_energy_Wh_l,
                    "mass_fractions": pack.mass_fractions,
                }

    return result


def calculate_all_reference_cases(
    cases: list[PhysicsReferenceCase],
) -> list[dict[str, Any]]:
    return [calculate_reference_case(case) for case in cases]


def write_reference_results(
    cases: list[PhysicsReferenceCase],
    output_path: Path | None = None,
) -> Path:
    destination = (
        output_path
        or PROJECT_ROOT / "reports" / "reference" / "phase2_reference_cases.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    config_path = PROJECT_ROOT / "configs" / "physics_reference_cases.yaml"
    code_paths = [
        *PROJECT_ROOT.glob("src/battery_frontier/physics/*.py"),
        PROJECT_ROOT / "src" / "battery_frontier" / "schemas.py",
    ]
    code_hashes = hash_files(code_paths, PROJECT_ROOT)
    code_snapshot_sha256 = hashlib.sha256(
        json.dumps(code_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()
    payload = {
        "phase": "2",
        "claim_status": "calculation fixtures; not experimental benchmarks",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "config_sha256": sha256_file(config_path),
        "code_hashes": code_hashes,
        "code_snapshot_sha256": code_snapshot_sha256,
        "cases": calculate_all_reference_cases(cases),
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination
