from __future__ import annotations

FARADAY_CONSTANT_C_PER_MOL = 96485.33212
SECONDS_PER_HOUR = 3600.0
GRAMS_PER_KILOGRAM = 1000.0


def theoretical_specific_capacity_mAh_g(
    electrons_transferred: float,
    reaction_basis_molar_mass_g_mol: float,
) -> float:
    """Return ideal capacity on the declared complete reaction-mass basis.

    Numerically, mAh/g equals Ah/kg. The caller is responsible for including
    every active reactant whose mass belongs in the intended comparison basis.
    """
    if electrons_transferred <= 0:
        raise ValueError("electrons_transferred must be positive")
    if reaction_basis_molar_mass_g_mol <= 0:
        raise ValueError("reaction_basis_molar_mass_g_mol must be positive")
    return (
        electrons_transferred
        * FARADAY_CONSTANT_C_PER_MOL
        / SECONDS_PER_HOUR
        * GRAMS_PER_KILOGRAM
        / reaction_basis_molar_mass_g_mol
    )


def theoretical_specific_energy_Wh_kg(
    specific_capacity_mAh_g: float,
    average_discharge_voltage_v: float,
) -> float:
    """Return ideal specific energy on the capacity's declared mass basis."""
    if specific_capacity_mAh_g <= 0:
        raise ValueError("specific_capacity_mAh_g must be positive")
    if average_discharge_voltage_v <= 0:
        raise ValueError("average_discharge_voltage_v must be positive")
    return specific_capacity_mAh_g * average_discharge_voltage_v
