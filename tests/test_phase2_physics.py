import json

import pytest

from battery_frontier import __version__
from battery_frontier.physics.bom import (
    CellBillOfMaterials,
    CellComponent,
    PackBillOfMaterials,
    PackComponent,
)
from battery_frontier.physics.reference_cases import (
    calculate_all_reference_cases,
    write_reference_results,
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
from battery_frontier.registry import load_registries


def test_full_reaction_mass_basis_and_balance() -> None:
    reaction = ElectrochemicalReaction(
        electrons_transferred=16,
        mass_basis_description="Li plus S8",
        species=(
            ReactionSpecies("Lithium", "Li", ReactionSide.REACTANT, 16, 6.94, True),
            ReactionSpecies("Sulfur", "S8", ReactionSide.REACTANT, 1, 256.48, True),
            ReactionSpecies("Lithium sulfide", "Li2S", ReactionSide.PRODUCT, 8, 45.94),
        ),
    )
    reaction.validate_mass_balance(1e-9)

    assert reaction.equation == "16 Li + S8 -> 8 Li2S"
    assert reaction.mass_basis_molar_mass_g_mol == pytest.approx(367.52)
    assert reaction.theoretical_specific_capacity_mAh_g == pytest.approx(1166.8037)


def test_mass_balance_failure_is_rejected() -> None:
    reaction = ElectrochemicalReaction(
        electrons_transferred=1,
        mass_basis_description="invalid fixture",
        species=(
            ReactionSpecies("A", "A", ReactionSide.REACTANT, 1, 10, True),
            ReactionSpecies("B", "B", ReactionSide.PRODUCT, 1, 20),
        ),
    )
    with pytest.raises(ValueError, match="mass balance exceeds tolerance"):
        reaction.validate_mass_balance(0.01)


def test_voltage_profile_integrates_capacity_weighted_voltage() -> None:
    profile = VoltageProfile(
        (
            VoltageSegment("upper", 0.25, 2.35),
            VoltageSegment("lower", 0.75, 2.10),
        )
    )
    assert profile.average_voltage_v == pytest.approx(2.1625)
    assert profile.specific_energy_Wh_kg(1000) == pytest.approx(2162.5)


def test_positive_interval_propagation_is_conservative() -> None:
    capacity = theoretical_capacity_interval_mAh_g(
        PositiveInterval(1, 1, 1, "mol e-/reaction"),
        PositiveInterval(10, 9, 11, "g/mol"),
    )
    energy = product_interval(
        capacity,
        PositiveInterval(3.0, 2.8, 3.2, "V"),
        unit="Wh/kg",
    )

    assert capacity.lower < capacity.nominal < capacity.upper
    assert energy.lower < energy.nominal < energy.upper


def test_cell_and_pack_bills_of_materials_expose_overhead() -> None:
    cell = CellBillOfMaterials(
        components=(
            CellComponent("active", "active", 600, True, 500),
            CellComponent("inactive", "inactive", 400, False, 300),
        ),
        active_specific_energy_Wh_kg=1000,
        capacity_utilization=0.8,
        voltage_efficiency=0.9,
        discharge_efficiency=0.95,
    )
    pack = PackBillOfMaterials(
        components=(
            PackComponent("cells", "cells", 700, True, 560),
            PackComponent("overhead", "overhead", 300, False, 240),
        ),
        cell_specific_energy_Wh_kg=cell.specific_energy_Wh_kg,
        discharge_efficiency=0.96,
    )

    assert cell.active_mass_fraction == pytest.approx(0.6)
    assert cell.specific_energy_Wh_kg == pytest.approx(410.4)
    assert cell.volumetric_energy_Wh_l == pytest.approx(513.0)
    assert pack.cell_mass_fraction == pytest.approx(0.7)
    assert pack.specific_energy_Wh_kg == pytest.approx(275.7888)
    assert pack.volumetric_energy_Wh_l == pytest.approx(344.736)


def test_gravimetric_to_volumetric_requires_declared_packing() -> None:
    assert gravimetric_to_volumetric_energy_Wh_l(250, 2.0, 0.65) == pytest.approx(325)


def test_registered_reference_cases_calculate_all_boundaries() -> None:
    registries = load_registries()
    results = calculate_all_reference_cases(registries.physics_reference_cases)
    by_id = {result["id"]: result for result in results}

    lithium = by_id["reference.lithium_metal_capacity"]
    sulfur = by_id["reference.lithium_sulfur_system_boundaries"]
    assert lithium["theoretical_specific_capacity_mAh_g"] == pytest.approx(3861.8849)
    assert sulfur["active_specific_energy_Wh_kg"] > sulfur["cell"]["specific_energy_Wh_kg"]
    assert sulfur["cell"]["specific_energy_Wh_kg"] > sulfur["pack"]["specific_energy_Wh_kg"]


def test_reference_artifact_contains_code_and_config_provenance(tmp_path) -> None:
    registries = load_registries()
    path = write_reference_results(
        registries.physics_reference_cases,
        output_path=tmp_path / "reference.json",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["package_version"] == __version__
    assert payload["config_sha256"]
    assert payload["code_snapshot_sha256"]
    assert payload["code_hashes"]
    assert len(payload["cases"]) == 2
