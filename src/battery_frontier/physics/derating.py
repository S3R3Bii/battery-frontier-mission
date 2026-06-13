from __future__ import annotations

from dataclasses import dataclass


def _fraction(name: str, value: float, *, allow_zero: bool = False) -> float:
    lower_ok = value >= 0 if allow_zero else value > 0
    if not lower_ok or value > 1:
        bracket = "[0, 1]" if allow_zero else "(0, 1]"
        raise ValueError(f"{name} must be in {bracket}")
    return value


@dataclass(frozen=True)
class CellDerating:
    active_material_mass_fraction: float
    active_material_utilization: float
    average_voltage_efficiency: float

    def __post_init__(self) -> None:
        _fraction("active_material_mass_fraction", self.active_material_mass_fraction)
        _fraction("active_material_utilization", self.active_material_utilization)
        _fraction("average_voltage_efficiency", self.average_voltage_efficiency)

    def apply(self, active_material_specific_energy_Wh_kg: float) -> float:
        if active_material_specific_energy_Wh_kg < 0:
            raise ValueError("active material specific energy cannot be negative")
        return (
            active_material_specific_energy_Wh_kg
            * self.active_material_mass_fraction
            * self.active_material_utilization
            * self.average_voltage_efficiency
        )


@dataclass(frozen=True)
class PackDerating:
    cell_mass_fraction_of_pack: float
    pack_discharge_efficiency: float

    def __post_init__(self) -> None:
        _fraction("cell_mass_fraction_of_pack", self.cell_mass_fraction_of_pack)
        _fraction("pack_discharge_efficiency", self.pack_discharge_efficiency)

    def apply(self, cell_specific_energy_Wh_kg: float) -> float:
        if cell_specific_energy_Wh_kg < 0:
            raise ValueError("cell specific energy cannot be negative")
        return (
            cell_specific_energy_Wh_kg
            * self.cell_mass_fraction_of_pack
            * self.pack_discharge_efficiency
        )


@dataclass(frozen=True)
class InstalledUseDerating:
    pack_mass_fraction_of_installed_system: float
    usable_depth_of_discharge: float
    state_of_health: float
    thermal_availability: float
    reserve_fraction: float
    powertrain_efficiency: float

    def __post_init__(self) -> None:
        _fraction(
            "pack_mass_fraction_of_installed_system",
            self.pack_mass_fraction_of_installed_system,
        )
        _fraction("usable_depth_of_discharge", self.usable_depth_of_discharge)
        _fraction("state_of_health", self.state_of_health)
        _fraction("thermal_availability", self.thermal_availability)
        _fraction("reserve_fraction", self.reserve_fraction, allow_zero=True)
        if self.reserve_fraction == 1:
            raise ValueError("reserve_fraction must be below 1")
        _fraction("powertrain_efficiency", self.powertrain_efficiency)

    def apply(self, pack_specific_energy_Wh_kg: float) -> float:
        if pack_specific_energy_Wh_kg < 0:
            raise ValueError("pack specific energy cannot be negative")
        return (
            pack_specific_energy_Wh_kg
            * self.pack_mass_fraction_of_installed_system
            * self.usable_depth_of_discharge
            * self.state_of_health
            * self.thermal_availability
            * (1 - self.reserve_fraction)
            * self.powertrain_efficiency
        )

