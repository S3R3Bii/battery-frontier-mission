from __future__ import annotations

from dataclasses import dataclass

STANDARD_GRAVITY_M_S2 = 9.80665
JOULES_PER_WH = 3600.0


def steady_level_cruise_mechanical_energy_Wh(
    aircraft_mass_kg: float,
    route_distance_km: float,
    lift_to_drag_ratio: float,
) -> float:
    """Return the first-order mechanical work needed for steady level cruise."""
    if aircraft_mass_kg <= 0:
        raise ValueError("aircraft_mass_kg must be positive")
    if route_distance_km <= 0:
        raise ValueError("route_distance_km must be positive")
    if lift_to_drag_ratio <= 0:
        raise ValueError("lift_to_drag_ratio must be positive")
    distance_m = route_distance_km * 1000.0
    drag_n = aircraft_mass_kg * STANDARD_GRAVITY_M_S2 / lift_to_drag_ratio
    return drag_n * distance_m / JOULES_PER_WH


@dataclass(frozen=True)
class MissionEnergyFactors:
    propulsion_efficiency: float
    usable_depth_of_discharge: float
    state_of_health: float
    thermal_availability: float
    reserve_fraction: float
    non_cruise_energy_fraction: float

    def __post_init__(self) -> None:
        unit_fractions = {
            "propulsion_efficiency": self.propulsion_efficiency,
            "usable_depth_of_discharge": self.usable_depth_of_discharge,
            "state_of_health": self.state_of_health,
            "thermal_availability": self.thermal_availability,
        }
        for name, value in unit_fractions.items():
            if not 0 < value <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
        if not 0 < self.reserve_fraction < 1:
            raise ValueError("reserve_fraction must be in (0, 1)")
        if self.non_cruise_energy_fraction < 0:
            raise ValueError("non_cruise_energy_fraction cannot be negative")

    def nominal_battery_energy_Wh(self, cruise_mechanical_energy_Wh: float) -> float:
        if cruise_mechanical_energy_Wh <= 0:
            raise ValueError("cruise mechanical energy must be positive")
        availability = (
            self.propulsion_efficiency
            * self.usable_depth_of_discharge
            * self.state_of_health
            * self.thermal_availability
            * (1 - self.reserve_fraction)
        )
        return cruise_mechanical_energy_Wh * (1 + self.non_cruise_energy_fraction) / availability


def required_pack_specific_energy_Wh_kg(
    nominal_battery_energy_Wh: float,
    aircraft_mass_kg: float,
    battery_mass_fraction: float,
) -> float:
    if nominal_battery_energy_Wh <= 0:
        raise ValueError("nominal_battery_energy_Wh must be positive")
    if aircraft_mass_kg <= 0:
        raise ValueError("aircraft_mass_kg must be positive")
    if not 0 < battery_mass_fraction < 1:
        raise ValueError("battery_mass_fraction must be in (0, 1)")
    battery_mass_kg = aircraft_mass_kg * battery_mass_fraction
    return nominal_battery_energy_Wh / battery_mass_kg
