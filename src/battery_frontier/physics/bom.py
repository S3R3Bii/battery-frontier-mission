from __future__ import annotations

from dataclasses import dataclass


def _efficiency(name: str, value: float) -> float:
    if not 0 < value <= 1:
        raise ValueError(f"{name} must be in (0, 1]")
    return value


@dataclass(frozen=True)
class CellComponent:
    name: str
    category: str
    mass_g: float
    is_active_reactant: bool = False
    volume_ml: float | None = None

    def __post_init__(self) -> None:
        if self.mass_g <= 0:
            raise ValueError("component mass must be positive")
        if self.volume_ml is not None and self.volume_ml <= 0:
            raise ValueError("component volume must be positive")


@dataclass(frozen=True)
class CellBillOfMaterials:
    components: tuple[CellComponent, ...]
    active_specific_energy_Wh_kg: float
    capacity_utilization: float
    voltage_efficiency: float
    discharge_efficiency: float

    def __post_init__(self) -> None:
        if not self.components:
            raise ValueError("cell bill of materials requires components")
        if self.active_specific_energy_Wh_kg < 0:
            raise ValueError("active specific energy cannot be negative")
        if not any(component.is_active_reactant for component in self.components):
            raise ValueError("cell bill of materials requires active-reactant mass")
        _efficiency("capacity_utilization", self.capacity_utilization)
        _efficiency("voltage_efficiency", self.voltage_efficiency)
        _efficiency("discharge_efficiency", self.discharge_efficiency)

    @property
    def total_mass_g(self) -> float:
        return sum(component.mass_g for component in self.components)

    @property
    def active_reactant_mass_g(self) -> float:
        return sum(
            component.mass_g
            for component in self.components
            if component.is_active_reactant
        )

    @property
    def active_mass_fraction(self) -> float:
        return self.active_reactant_mass_g / self.total_mass_g

    @property
    def nominal_energy_Wh(self) -> float:
        active_mass_kg = self.active_reactant_mass_g / 1000.0
        return (
            self.active_specific_energy_Wh_kg
            * active_mass_kg
            * self.capacity_utilization
            * self.voltage_efficiency
            * self.discharge_efficiency
        )

    @property
    def specific_energy_Wh_kg(self) -> float:
        return self.nominal_energy_Wh / (self.total_mass_g / 1000.0)

    @property
    def total_volume_l(self) -> float | None:
        if any(component.volume_ml is None for component in self.components):
            return None
        return sum(component.volume_ml or 0.0 for component in self.components) / 1000.0

    @property
    def volumetric_energy_Wh_l(self) -> float | None:
        volume_l = self.total_volume_l
        if volume_l is None:
            return None
        return self.nominal_energy_Wh / volume_l

    @property
    def mass_fractions(self) -> dict[str, float]:
        return {
            component.name: component.mass_g / self.total_mass_g
            for component in self.components
        }


@dataclass(frozen=True)
class PackComponent:
    name: str
    category: str
    mass_kg: float
    is_cell_mass: bool = False
    volume_l: float | None = None

    def __post_init__(self) -> None:
        if self.mass_kg <= 0:
            raise ValueError("component mass must be positive")
        if self.volume_l is not None and self.volume_l <= 0:
            raise ValueError("component volume must be positive")


@dataclass(frozen=True)
class PackBillOfMaterials:
    components: tuple[PackComponent, ...]
    cell_specific_energy_Wh_kg: float
    discharge_efficiency: float

    def __post_init__(self) -> None:
        if not self.components:
            raise ValueError("pack bill of materials requires components")
        if self.cell_specific_energy_Wh_kg < 0:
            raise ValueError("cell specific energy cannot be negative")
        if not any(component.is_cell_mass for component in self.components):
            raise ValueError("pack bill of materials requires cell mass")
        _efficiency("discharge_efficiency", self.discharge_efficiency)

    @property
    def total_mass_kg(self) -> float:
        return sum(component.mass_kg for component in self.components)

    @property
    def cell_mass_kg(self) -> float:
        return sum(
            component.mass_kg for component in self.components if component.is_cell_mass
        )

    @property
    def cell_mass_fraction(self) -> float:
        return self.cell_mass_kg / self.total_mass_kg

    @property
    def nominal_energy_Wh(self) -> float:
        return (
            self.cell_specific_energy_Wh_kg
            * self.cell_mass_kg
            * self.discharge_efficiency
        )

    @property
    def specific_energy_Wh_kg(self) -> float:
        return self.nominal_energy_Wh / self.total_mass_kg

    @property
    def total_volume_l(self) -> float | None:
        if any(component.volume_l is None for component in self.components):
            return None
        return sum(component.volume_l or 0.0 for component in self.components)

    @property
    def volumetric_energy_Wh_l(self) -> float | None:
        volume_l = self.total_volume_l
        if volume_l is None:
            return None
        return self.nominal_energy_Wh / volume_l

    @property
    def mass_fractions(self) -> dict[str, float]:
        return {
            component.name: component.mass_kg / self.total_mass_kg
            for component in self.components
        }

