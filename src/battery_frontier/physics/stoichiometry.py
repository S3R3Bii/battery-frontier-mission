from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from battery_frontier.physics.electrochemistry import (
    theoretical_specific_capacity_mAh_g,
)


class ReactionSide(StrEnum):
    REACTANT = "reactant"
    PRODUCT = "product"


@dataclass(frozen=True)
class ReactionSpecies:
    name: str
    formula: str
    side: ReactionSide
    stoichiometric_coefficient: float
    molar_mass_g_mol: float
    included_in_mass_basis: bool = False

    def __post_init__(self) -> None:
        if self.stoichiometric_coefficient <= 0:
            raise ValueError("stoichiometric coefficient must be positive")
        if self.molar_mass_g_mol <= 0:
            raise ValueError("molar mass must be positive")
        if self.included_in_mass_basis and self.side != ReactionSide.REACTANT:
            raise ValueError("mass-basis species must be reactants")

    @property
    def reaction_mass_g_mol(self) -> float:
        return self.stoichiometric_coefficient * self.molar_mass_g_mol


@dataclass(frozen=True)
class ElectrochemicalReaction:
    electrons_transferred: float
    species: tuple[ReactionSpecies, ...]
    mass_basis_description: str

    def __post_init__(self) -> None:
        if self.electrons_transferred <= 0:
            raise ValueError("electrons_transferred must be positive")
        if len(self.species) < 2:
            raise ValueError("a reaction requires at least two species")
        if not any(item.side == ReactionSide.REACTANT for item in self.species):
            raise ValueError("a reaction requires a reactant")
        if not any(item.side == ReactionSide.PRODUCT for item in self.species):
            raise ValueError("a reaction requires a product")
        if not any(item.included_in_mass_basis for item in self.species):
            raise ValueError("a reaction requires an explicit mass basis")

    @property
    def reactant_mass_g_mol(self) -> float:
        return sum(
            item.reaction_mass_g_mol
            for item in self.species
            if item.side == ReactionSide.REACTANT
        )

    @property
    def product_mass_g_mol(self) -> float:
        return sum(
            item.reaction_mass_g_mol
            for item in self.species
            if item.side == ReactionSide.PRODUCT
        )

    @property
    def mass_basis_molar_mass_g_mol(self) -> float:
        return sum(
            item.reaction_mass_g_mol
            for item in self.species
            if item.included_in_mass_basis
        )

    @property
    def mass_balance_relative_error(self) -> float:
        reference_mass = max(self.reactant_mass_g_mol, self.product_mass_g_mol)
        if reference_mass == 0:
            return 0.0
        return abs(self.reactant_mass_g_mol - self.product_mass_g_mol) / reference_mass

    def validate_mass_balance(self, tolerance_fraction: float) -> None:
        if not 0 <= tolerance_fraction <= 1:
            raise ValueError("tolerance_fraction must be in [0, 1]")
        if self.mass_balance_relative_error > tolerance_fraction:
            raise ValueError(
                "reaction mass balance exceeds tolerance: "
                f"{self.mass_balance_relative_error:.6g} > {tolerance_fraction:.6g}"
            )

    @property
    def theoretical_specific_capacity_mAh_g(self) -> float:
        return theoretical_specific_capacity_mAh_g(
            self.electrons_transferred,
            self.mass_basis_molar_mass_g_mol,
        )

    @property
    def equation(self) -> str:
        def render(side: ReactionSide) -> str:
            terms = []
            for item in self.species:
                if item.side != side:
                    continue
                coefficient = (
                    ""
                    if item.stoichiometric_coefficient == 1
                    else f"{item.stoichiometric_coefficient:g} "
                )
                terms.append(f"{coefficient}{item.formula}")
            return " + ".join(terms)

        return f"{render(ReactionSide.REACTANT)} -> {render(ReactionSide.PRODUCT)}"

