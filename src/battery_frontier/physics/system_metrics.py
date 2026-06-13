from __future__ import annotations


def gravimetric_to_volumetric_energy_Wh_l(
    specific_energy_Wh_kg: float,
    material_density_kg_l: float,
    packing_fraction: float = 1.0,
) -> float:
    """Convert a gravimetric basis to a declared packed volumetric basis."""
    if specific_energy_Wh_kg < 0:
        raise ValueError("specific_energy_Wh_kg cannot be negative")
    if material_density_kg_l <= 0:
        raise ValueError("material_density_kg_l must be positive")
    if not 0 < packing_fraction <= 1:
        raise ValueError("packing_fraction must be in (0, 1]")
    return specific_energy_Wh_kg * material_density_kg_l * packing_fraction

