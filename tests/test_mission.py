import pytest

from battery_frontier.aviation.mission import (
    MissionEnergyFactors,
    required_pack_specific_energy_Wh_kg,
    steady_level_cruise_mechanical_energy_Wh,
)


def test_cruise_energy_matches_force_times_distance() -> None:
    result = steady_level_cruise_mechanical_energy_Wh(
        aircraft_mass_kg=1000,
        route_distance_km=100,
        lift_to_drag_ratio=10,
    )
    assert result == pytest.approx(27240.6944, rel=1e-6)


def test_nominal_energy_increases_after_visible_penalties() -> None:
    mechanical = 100_000.0
    factors = MissionEnergyFactors(
        propulsion_efficiency=0.85,
        usable_depth_of_discharge=0.8,
        state_of_health=0.8,
        thermal_availability=0.95,
        reserve_fraction=0.2,
        non_cruise_energy_fraction=0.15,
    )
    nominal = factors.nominal_battery_energy_Wh(mechanical)
    required = required_pack_specific_energy_Wh_kg(nominal, 10_000, 0.4)
    assert nominal > mechanical
    assert required == pytest.approx(nominal / 4000)


@pytest.mark.parametrize("reserve_fraction", [0, -0.1, 1.0])
def test_energy_factors_reject_nonphysical_reserve(reserve_fraction: float) -> None:
    with pytest.raises(ValueError):
        MissionEnergyFactors(
            propulsion_efficiency=0.85,
            usable_depth_of_discharge=0.8,
            state_of_health=0.8,
            thermal_availability=0.95,
            reserve_fraction=reserve_fraction,
            non_cruise_energy_fraction=0.15,
        )


@pytest.mark.parametrize("energy", [0, -1])
def test_required_pack_specific_energy_rejects_nonpositive_energy(energy: float) -> None:
    with pytest.raises(ValueError):
        required_pack_specific_energy_Wh_kg(energy, 10_000, 0.4)
