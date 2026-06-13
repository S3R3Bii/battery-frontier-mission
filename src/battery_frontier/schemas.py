from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceClass(StrEnum):
    KNOWN_EXPERIMENTAL = "known_experimental"
    LITERATURE_PROJECTION = "literature_projection"
    SIMULATION_ESTIMATE = "simulation_estimate"
    THEORETICAL_LIMIT = "theoretical_limit"
    SPECULATIVE_HYPOTHESIS = "speculative_hypothesis"


class UncertaintyKind(StrEnum):
    FIXED = "fixed"
    RANGE = "range"
    NOT_QUANTIFIED = "not_quantified"


class Uncertainty(StrictModel):
    kind: UncertaintyKind
    lower: float | None = None
    upper: float | None = None
    note: str = Field(min_length=10)

    @model_validator(mode="after")
    def validate_bounds(self) -> Uncertainty:
        if self.kind == UncertaintyKind.RANGE:
            if self.lower is None or self.upper is None:
                raise ValueError("range uncertainty requires lower and upper bounds")
            if self.lower > self.upper:
                raise ValueError("uncertainty lower bound cannot exceed upper bound")
        elif self.lower is not None or self.upper is not None:
            raise ValueError("bounds are only valid for range uncertainty")
        return self


class Assumption(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    version: int = Field(ge=1)
    name: str
    category: str
    boundary: str
    value: float | int | str | bool
    unit: str
    evidence_class: EvidenceClass
    status: str
    uncertainty: Uncertainty
    citation_ids: list[str]
    rationale: str = Field(min_length=10)
    sensitivity: str = Field(min_length=10)
    owner: str
    review_due: date
    tags: list[str]

    @model_validator(mode="after")
    def validate_fraction(self) -> Assumption:
        if self.unit == "fraction":
            value = float(self.value)
            if not 0 <= value <= 1:
                raise ValueError("fraction assumptions must be in [0, 1]")
            if self.uncertainty.kind == UncertaintyKind.RANGE:
                assert self.uncertainty.lower is not None
                assert self.uncertainty.upper is not None
                if not 0 <= self.uncertainty.lower <= self.uncertainty.upper <= 1:
                    raise ValueError("fraction uncertainty bounds must be in [0, 1]")
        return self


class AviationScenario(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    version: int = Field(ge=1)
    name: str
    evidence_class: EvidenceClass
    status: str
    description: str
    route_distance_km: float = Field(gt=0)
    aircraft_mass_kg: float = Field(gt=0)
    payload_mass_kg: float = Field(ge=0)
    battery_mass_fraction: float = Field(gt=0, lt=1)
    lift_to_drag_ratio: float = Field(gt=0)
    propulsion_efficiency: float = Field(gt=0, le=1)
    usable_depth_of_discharge: float = Field(gt=0, le=1)
    end_of_life_state_of_health: float = Field(gt=0, le=1)
    thermal_availability: float = Field(gt=0, le=1)
    reserve_fraction: float = Field(gt=0, lt=1)
    non_cruise_energy_fraction: float = Field(ge=0)
    cruise_speed_m_per_s: float = Field(gt=0)
    uncertainty_note: str = Field(min_length=20)
    citation_ids: list[str]

    @model_validator(mode="after")
    def validate_masses(self) -> AviationScenario:
        if self.payload_mass_kg >= self.aircraft_mass_kg:
            raise ValueError("payload mass must be below aircraft mass")
        return self


class SegmentedMissionCase(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    version: int = Field(ge=1)
    name: str
    evidence_class: EvidenceClass
    status: str
    description: str
    operating_empty_mass_excluding_battery_kg: float = Field(gt=0)
    maximum_takeoff_mass_kg: float = Field(gt=0)
    payload_mass_kg: float = Field(ge=0)
    maximum_payload_kg: float = Field(gt=0)
    route_distance_km: float = Field(gt=0)
    range_search_upper_km: float = Field(gt=0)
    cruise_altitude_m: float = Field(gt=0)
    cruise_speed_m_per_s: float = Field(gt=0)
    climb_speed_m_per_s: float = Field(gt=0)
    climb_rate_m_per_s: float = Field(gt=0)
    descent_speed_m_per_s: float = Field(gt=0)
    descent_rate_m_per_s: float = Field(gt=0)
    reserve_speed_m_per_s: float = Field(gt=0)
    cruise_lift_to_drag_ratio: float = Field(gt=0)
    climb_lift_to_drag_ratio: float = Field(gt=0)
    descent_lift_to_drag_ratio: float = Field(gt=0)
    reserve_lift_to_drag_ratio: float = Field(gt=0)
    descent_propulsive_fraction: float = Field(ge=0, le=1)
    propulsion_efficiency: float = Field(gt=0, le=1)
    auxiliary_power_kw: float = Field(ge=0)
    taxi_duration_min: float = Field(ge=0)
    taxi_propulsion_power_kw: float = Field(ge=0)
    reserve_loiter_duration_min: float = Field(gt=0)
    pack_specific_energy_Wh_kg: float = Field(gt=0)
    pack_specific_power_W_kg: float = Field(gt=0)
    maximum_continuous_c_rate: float = Field(gt=0)
    usable_depth_of_discharge: float = Field(gt=0, le=1)
    end_of_life_state_of_health: float = Field(gt=0, le=1)
    thermal_availability: float = Field(gt=0, le=1)
    maximum_battery_mass_fraction: float = Field(gt=0, lt=1)
    peak_power_margin_fraction: float = Field(ge=0)
    uncertainty_note: str = Field(min_length=20)
    citation_ids: list[str]

    @model_validator(mode="after")
    def validate_segmented_mission(self) -> SegmentedMissionCase:
        if self.payload_mass_kg > self.maximum_payload_kg:
            raise ValueError("payload mass cannot exceed maximum payload")
        fixed_mass = self.operating_empty_mass_excluding_battery_kg + self.payload_mass_kg
        if fixed_mass >= self.maximum_takeoff_mass_kg:
            raise ValueError("empty mass plus payload must leave positive battery mass")
        if self.route_distance_km > self.range_search_upper_km:
            raise ValueError("route distance cannot exceed range-search upper bound")
        return self


class ChemistryFamily(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    name: str
    evidence_class: EvidenceClass
    status: str
    scope: str
    known_constraints: list[str] = Field(min_length=1)
    required_metrics: list[str] = Field(min_length=1)
    citation_ids: list[str]


class Citation(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    title: str
    authors: list[str] = Field(min_length=1)
    year: int = Field(ge=1800, le=2100)
    doi: str | None = None
    url: HttpUrl
    source_type: str
    peer_reviewed: bool
    metadata_status: str


class DataSource(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    name: str
    url: HttpUrl
    access_date: date | None = None
    license_status: str
    license_note: str
    variables: list[str] = Field(min_length=1)
    reliability_rating: int = Field(ge=1, le=5)
    update_frequency: str
    limitations: str
    ingestion_status: str
    citation_ids: list[str]


class AircraftSystem(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    manufacturer: str
    vehicle_name: str
    aircraft_class: str
    role: str
    range_km: float | None = Field(default=None, gt=0)
    cruise_speed_kmh: float | None = Field(default=None, gt=0)
    max_speed_kmh: float | None = Field(default=None, gt=0)
    payload_kg: float | None = Field(default=None, gt=0)
    passenger_capacity: int | None = Field(default=None, ge=0)
    mtow_kg: float | None = Field(default=None, gt=0)
    battery_capacity_kWh: float | None = Field(default=None, gt=0)
    motor_count: int | None = Field(default=None, ge=0)
    motor_power_kW: float | None = Field(default=None, gt=0)
    propulsor_count: int | None = Field(default=None, ge=0)
    certification_status: str
    source_url: HttpUrl
    source_type: str
    source_confidence: str
    values_status: str
    date_accessed: date
    limitations: str = Field(min_length=20)

    @model_validator(mode="after")
    def validate_source_boundary(self) -> AircraftSystem:
        allowed_values = {"official", "official_partial", "third_party", "estimated"}
        if self.values_status not in allowed_values:
            raise ValueError(f"values_status must be one of {sorted(allowed_values)}")
        if not self.source_url:
            raise ValueError("manufacturer example requires a source URL")
        return self


class PropulsionSystem(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    manufacturer: str
    system_name: str
    system_type: str
    use_case: str
    max_power_kW: float | None = Field(default=None, gt=0)
    continuous_power_kW: float | None = Field(default=None, gt=0)
    propulsor_count: int | None = Field(default=None, ge=0)
    aircraft_examples: list[str]
    source_url: HttpUrl
    source_type: str
    source_confidence: str
    values_status: str
    date_accessed: date
    limitations: str = Field(min_length=20)


class DatasetCandidate(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    name: str
    url: HttpUrl
    doi: str | None = None
    category: str
    license_status: str
    system_boundary: str
    variables: list[str] = Field(min_length=1)
    likely_usefulness: str = Field(min_length=20)
    ingestion_risk: str
    downloadable: bool
    redistributable: bool | None = None
    measured_performance: bool
    metadata_only: bool
    priority: int = Field(ge=1, le=5)
    status: str
    date_accessed: date
    limitations: str = Field(min_length=20)


class ReactionSide(StrEnum):
    REACTANT = "reactant"
    PRODUCT = "product"


class ReactionSpeciesInput(StrictModel):
    name: str
    formula: str
    side: ReactionSide
    stoichiometric_coefficient: float = Field(gt=0)
    molar_mass_g_mol: float = Field(gt=0)
    included_in_mass_basis: bool = False


class VoltageSegmentInput(StrictModel):
    label: str
    capacity_fraction: float = Field(gt=0, le=1)
    average_voltage_v: float = Field(gt=0)


class CellComponentInput(StrictModel):
    name: str
    category: str
    mass_g: float = Field(gt=0)
    is_active_reactant: bool = False
    volume_ml: float | None = Field(default=None, gt=0)


class CellDesignInput(StrictModel):
    components: list[CellComponentInput] = Field(min_length=1)
    capacity_utilization: float = Field(gt=0, le=1)
    voltage_efficiency: float = Field(gt=0, le=1)
    discharge_efficiency: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def validate_active_mass(self) -> CellDesignInput:
        if not any(component.is_active_reactant for component in self.components):
            raise ValueError("cell design requires at least one active-reactant component")
        return self


class PackComponentInput(StrictModel):
    name: str
    category: str
    mass_kg: float = Field(gt=0)
    is_cell_mass: bool = False
    volume_l: float | None = Field(default=None, gt=0)


class PackDesignInput(StrictModel):
    components: list[PackComponentInput] = Field(min_length=1)
    discharge_efficiency: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def validate_cell_mass(self) -> PackDesignInput:
        if not any(component.is_cell_mass for component in self.components):
            raise ValueError("pack design requires at least one cell-mass component")
        return self


class RangeInput(StrictModel):
    nominal: float = Field(gt=0)
    lower: float = Field(gt=0)
    upper: float = Field(gt=0)
    unit: str

    @model_validator(mode="after")
    def validate_order(self) -> RangeInput:
        if not self.lower <= self.nominal <= self.upper:
            raise ValueError("range must satisfy lower <= nominal <= upper")
        return self


class PhysicsReferenceCase(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_.-]+$")
    name: str
    evidence_class: EvidenceClass
    status: str
    description: str
    mass_basis_description: str
    electrons_transferred: float = Field(gt=0)
    species: list[ReactionSpeciesInput] = Field(min_length=2)
    mass_balance_tolerance_fraction: float = Field(ge=0, le=0.05)
    voltage_profile: list[VoltageSegmentInput] = Field(default_factory=list)
    reaction_molar_mass_range: RangeInput | None = None
    average_voltage_range: RangeInput | None = None
    active_material_density_kg_l: float | None = Field(default=None, gt=0)
    electrode_packing_fraction: float | None = Field(default=None, gt=0, le=1)
    cell_design: CellDesignInput | None = None
    pack_design: PackDesignInput | None = None
    uncertainty_note: str = Field(min_length=20)
    citation_ids: list[str]

    @model_validator(mode="after")
    def validate_reference_case(self) -> PhysicsReferenceCase:
        if not any(species.side == ReactionSide.REACTANT for species in self.species):
            raise ValueError("reference reaction requires at least one reactant")
        if not any(species.side == ReactionSide.PRODUCT for species in self.species):
            raise ValueError("reference reaction requires at least one product")
        if not any(species.included_in_mass_basis for species in self.species):
            raise ValueError("reference reaction requires a declared mass basis")
        if any(
            species.included_in_mass_basis and species.side != ReactionSide.REACTANT
            for species in self.species
        ):
            raise ValueError("only reactants may be included in the reaction mass basis")
        reactant_mass = sum(
            species.stoichiometric_coefficient * species.molar_mass_g_mol
            for species in self.species
            if species.side == ReactionSide.REACTANT
        )
        product_mass = sum(
            species.stoichiometric_coefficient * species.molar_mass_g_mol
            for species in self.species
            if species.side == ReactionSide.PRODUCT
        )
        mass_balance_error = abs(reactant_mass - product_mass) / max(
            reactant_mass,
            product_mass,
        )
        if mass_balance_error > self.mass_balance_tolerance_fraction:
            raise ValueError("reference reaction exceeds its mass-balance tolerance")
        if self.voltage_profile:
            total_fraction = sum(segment.capacity_fraction for segment in self.voltage_profile)
            if abs(total_fraction - 1.0) > 1e-9:
                raise ValueError("voltage-profile capacity fractions must sum to 1")
        if (self.active_material_density_kg_l is None) != (
            self.electrode_packing_fraction is None
        ):
            raise ValueError("density and packing fraction must be supplied together")
        if self.cell_design is not None and not self.voltage_profile:
            raise ValueError("cell design requires a voltage profile")
        if self.pack_design is not None and self.cell_design is None:
            raise ValueError("pack design requires a cell design")
        if self.reaction_molar_mass_range is not None:
            if self.reaction_molar_mass_range.unit != "g/mol":
                raise ValueError("reaction molar-mass range must use g/mol")
            declared_mass_basis = sum(
                species.stoichiometric_coefficient * species.molar_mass_g_mol
                for species in self.species
                if species.included_in_mass_basis
            )
            if abs(self.reaction_molar_mass_range.nominal - declared_mass_basis) > 1e-9:
                raise ValueError("molar-mass nominal must match the declared reaction basis")
        if self.average_voltage_range is not None:
            if self.average_voltage_range.unit != "V":
                raise ValueError("average-voltage range must use V")
            profile_average = sum(
                segment.capacity_fraction * segment.average_voltage_v
                for segment in self.voltage_profile
            )
            if abs(self.average_voltage_range.nominal - profile_average) > 1e-9:
                raise ValueError("voltage-range nominal must match the voltage profile")
        return self
