from __future__ import annotations

from dataclasses import dataclass

from battery_frontier.physics.electrochemistry import (
    FARADAY_CONSTANT_C_PER_MOL,
    GRAMS_PER_KILOGRAM,
    SECONDS_PER_HOUR,
)


@dataclass(frozen=True)
class PositiveInterval:
    nominal: float
    lower: float
    upper: float
    unit: str

    def __post_init__(self) -> None:
        if self.lower <= 0:
            raise ValueError("interval lower bound must be positive")
        if not self.lower <= self.nominal <= self.upper:
            raise ValueError("interval must satisfy lower <= nominal <= upper")

    @property
    def relative_span(self) -> float:
        return (self.upper - self.lower) / self.nominal


def theoretical_capacity_interval_mAh_g(
    electrons_transferred: PositiveInterval,
    reaction_molar_mass_g_mol: PositiveInterval,
) -> PositiveInterval:
    """Propagate monotonic positive intervals through Faraday's law."""
    factor = FARADAY_CONSTANT_C_PER_MOL / SECONDS_PER_HOUR * GRAMS_PER_KILOGRAM
    return PositiveInterval(
        nominal=factor
        * electrons_transferred.nominal
        / reaction_molar_mass_g_mol.nominal,
        lower=factor * electrons_transferred.lower / reaction_molar_mass_g_mol.upper,
        upper=factor * electrons_transferred.upper / reaction_molar_mass_g_mol.lower,
        unit="mAh/g",
    )


def product_interval(
    left: PositiveInterval,
    right: PositiveInterval,
    *,
    unit: str,
) -> PositiveInterval:
    """Return the exact interval product for positive independent bounds."""
    return PositiveInterval(
        nominal=left.nominal * right.nominal,
        lower=left.lower * right.lower,
        upper=left.upper * right.upper,
        unit=unit,
    )

