from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoltageSegment:
    label: str
    capacity_fraction: float
    average_voltage_v: float

    def __post_init__(self) -> None:
        if not 0 < self.capacity_fraction <= 1:
            raise ValueError("capacity_fraction must be in (0, 1]")
        if self.average_voltage_v < 0:
            raise ValueError("average_voltage_v cannot be negative")


@dataclass(frozen=True)
class VoltageProfile:
    segments: tuple[VoltageSegment, ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("voltage profile requires at least one segment")
        total_fraction = sum(segment.capacity_fraction for segment in self.segments)
        if abs(total_fraction - 1.0) > 1e-9:
            raise ValueError("voltage-profile capacity fractions must sum to 1")

    @property
    def average_voltage_v(self) -> float:
        return sum(
            segment.capacity_fraction * segment.average_voltage_v
            for segment in self.segments
        )

    def specific_energy_Wh_kg(self, specific_capacity_mAh_g: float) -> float:
        if specific_capacity_mAh_g < 0:
            raise ValueError("specific_capacity_mAh_g cannot be negative")
        return specific_capacity_mAh_g * self.average_voltage_v

