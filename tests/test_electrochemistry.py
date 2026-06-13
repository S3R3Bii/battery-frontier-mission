import pytest

from battery_frontier.physics.electrochemistry import (
    theoretical_specific_capacity_mAh_g,
    theoretical_specific_energy_Wh_kg,
)


def test_lithium_metal_capacity_matches_faraday_law() -> None:
    capacity = theoretical_specific_capacity_mAh_g(
        electrons_transferred=1,
        reaction_basis_molar_mass_g_mol=6.94,
    )
    assert capacity == pytest.approx(3861.8849, rel=1e-6)


def test_specific_energy_preserves_mass_basis() -> None:
    assert theoretical_specific_energy_Wh_kg(200.0, 3.5) == pytest.approx(700.0)


@pytest.mark.parametrize(
    ("capacity", "voltage"),
    [(0, 3.5), (-1, 3.5), (200, 0), (200, -0.1)],
)
def test_specific_energy_rejects_nonphysical_inputs(
    capacity: float,
    voltage: float,
) -> None:
    with pytest.raises(ValueError):
        theoretical_specific_energy_Wh_kg(capacity, voltage)


@pytest.mark.parametrize(
    ("electrons", "molar_mass"),
    [(0, 10), (-1, 10), (1, 0), (1, -10)],
)
def test_capacity_rejects_nonphysical_inputs(electrons: float, molar_mass: float) -> None:
    with pytest.raises(ValueError):
        theoretical_specific_capacity_mAh_g(electrons, molar_mass)
