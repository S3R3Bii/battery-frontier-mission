from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from battery_frontier.aviation.mission import (
    JOULES_PER_WH,
    STANDARD_GRAVITY_M_S2,
)
from battery_frontier.schemas import SegmentedMissionCase


class SegmentKind(StrEnum):
    TAXI = "taxi"
    CLIMB = "climb"
    CRUISE = "cruise"
    RESERVE = "reserve"
    DESCENT = "descent"


@dataclass(frozen=True)
class MissionDefinition:
    name: str
    operating_empty_mass_excluding_battery_kg: float
    maximum_takeoff_mass_kg: float
    payload_mass_kg: float
    maximum_payload_kg: float
    route_distance_km: float
    range_search_upper_km: float
    cruise_altitude_m: float
    cruise_speed_m_per_s: float
    climb_speed_m_per_s: float
    climb_rate_m_per_s: float
    descent_speed_m_per_s: float
    descent_rate_m_per_s: float
    reserve_speed_m_per_s: float
    cruise_lift_to_drag_ratio: float
    climb_lift_to_drag_ratio: float
    descent_lift_to_drag_ratio: float
    reserve_lift_to_drag_ratio: float
    descent_propulsive_fraction: float
    propulsion_efficiency: float
    auxiliary_power_kw: float
    taxi_duration_min: float
    taxi_propulsion_power_kw: float
    reserve_loiter_duration_min: float
    pack_specific_energy_Wh_kg: float
    pack_specific_power_W_kg: float
    maximum_continuous_c_rate: float
    usable_depth_of_discharge: float
    end_of_life_state_of_health: float
    thermal_availability: float
    maximum_battery_mass_fraction: float
    peak_power_margin_fraction: float

    @property
    def fixed_mass_kg(self) -> float:
        return self.operating_empty_mass_excluding_battery_kg + self.payload_mass_kg

    @property
    def energy_availability_fraction(self) -> float:
        return (
            self.usable_depth_of_discharge
            * self.end_of_life_state_of_health
            * self.thermal_availability
        )

    @property
    def power_availability_fraction(self) -> float:
        return self.end_of_life_state_of_health * self.thermal_availability

    @property
    def climb_duration_s(self) -> float:
        return self.cruise_altitude_m / self.climb_rate_m_per_s

    @property
    def descent_duration_s(self) -> float:
        return self.cruise_altitude_m / self.descent_rate_m_per_s

    @property
    def climb_horizontal_distance_km(self) -> float:
        return self.climb_speed_m_per_s * self.climb_duration_s / 1000.0

    @property
    def descent_horizontal_distance_km(self) -> float:
        return self.descent_speed_m_per_s * self.descent_duration_s / 1000.0

    @property
    def minimum_route_distance_km(self) -> float:
        return self.climb_horizontal_distance_km + self.descent_horizontal_distance_km


@dataclass(frozen=True)
class MissionSegmentResult:
    name: str
    kind: SegmentKind
    duration_min: float
    horizontal_distance_km: float
    mechanical_energy_Wh: float
    electrical_energy_Wh: float
    average_electrical_power_W: float
    assumptions: str


@dataclass(frozen=True)
class MissionSolution:
    definition: MissionDefinition
    converged: bool
    feasible: bool
    iterations: int
    battery_mass_kg: float
    takeoff_mass_kg: float
    battery_mass_fraction: float
    terminal_electrical_energy_Wh: float
    nominal_battery_energy_Wh: float
    peak_electrical_power_W: float
    energy_limited_mass_kg: float
    specific_power_limited_mass_kg: float
    c_rate_limited_mass_kg: float
    limiting_constraint: str
    segments: tuple[MissionSegmentResult, ...]
    reasons: tuple[str, ...]


def _validate_mission_definition(definition: MissionDefinition) -> None:
    positive_fields = {
        "operating_empty_mass_excluding_battery_kg": (
            definition.operating_empty_mass_excluding_battery_kg
        ),
        "maximum_takeoff_mass_kg": definition.maximum_takeoff_mass_kg,
        "maximum_payload_kg": definition.maximum_payload_kg,
        "route_distance_km": definition.route_distance_km,
        "range_search_upper_km": definition.range_search_upper_km,
        "cruise_altitude_m": definition.cruise_altitude_m,
        "cruise_speed_m_per_s": definition.cruise_speed_m_per_s,
        "climb_speed_m_per_s": definition.climb_speed_m_per_s,
        "climb_rate_m_per_s": definition.climb_rate_m_per_s,
        "descent_speed_m_per_s": definition.descent_speed_m_per_s,
        "descent_rate_m_per_s": definition.descent_rate_m_per_s,
        "reserve_speed_m_per_s": definition.reserve_speed_m_per_s,
        "cruise_lift_to_drag_ratio": definition.cruise_lift_to_drag_ratio,
        "climb_lift_to_drag_ratio": definition.climb_lift_to_drag_ratio,
        "descent_lift_to_drag_ratio": definition.descent_lift_to_drag_ratio,
        "reserve_lift_to_drag_ratio": definition.reserve_lift_to_drag_ratio,
        "reserve_loiter_duration_min": definition.reserve_loiter_duration_min,
        "pack_specific_energy_Wh_kg": definition.pack_specific_energy_Wh_kg,
        "pack_specific_power_W_kg": definition.pack_specific_power_W_kg,
        "maximum_continuous_c_rate": definition.maximum_continuous_c_rate,
    }
    for name, value in positive_fields.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    if definition.payload_mass_kg < 0:
        raise ValueError("payload_mass_kg cannot be negative")
    if definition.fixed_mass_kg >= definition.maximum_takeoff_mass_kg:
        raise ValueError("empty mass plus payload must leave positive battery mass")
    if definition.route_distance_km > definition.range_search_upper_km:
        raise ValueError("route distance cannot exceed range-search upper bound")
    unit_interval_fields = {
        "descent_propulsive_fraction": definition.descent_propulsive_fraction,
        "propulsion_efficiency": definition.propulsion_efficiency,
        "usable_depth_of_discharge": definition.usable_depth_of_discharge,
        "end_of_life_state_of_health": definition.end_of_life_state_of_health,
        "thermal_availability": definition.thermal_availability,
    }
    for name, value in unit_interval_fields.items():
        if not 0 < value <= 1:
            raise ValueError(f"{name} must be in (0, 1]")
    if not 0 < definition.maximum_battery_mass_fraction < 1:
        raise ValueError("maximum_battery_mass_fraction must be in (0, 1)")
    if definition.auxiliary_power_kw < 0:
        raise ValueError("auxiliary_power_kw cannot be negative")
    if definition.taxi_duration_min < 0:
        raise ValueError("taxi_duration_min cannot be negative")
    if definition.taxi_propulsion_power_kw < 0:
        raise ValueError("taxi_propulsion_power_kw cannot be negative")
    if definition.peak_power_margin_fraction < 0:
        raise ValueError("peak_power_margin_fraction cannot be negative")


def mission_definition_from_case(case: SegmentedMissionCase) -> MissionDefinition:
    fields = MissionDefinition.__dataclass_fields__
    payload = case.model_dump()
    return MissionDefinition(**{name: payload[name] for name in fields})


def _drag_force_n(
    aircraft_mass_kg: float,
    lift_to_drag_ratio: float,
) -> float:
    return aircraft_mass_kg * STANDARD_GRAVITY_M_S2 / lift_to_drag_ratio


def _segment(
    *,
    name: str,
    kind: SegmentKind,
    duration_s: float,
    distance_m: float,
    mechanical_power_W: float,
    propulsion_efficiency: float,
    auxiliary_power_W: float,
    assumptions: str,
) -> MissionSegmentResult:
    if duration_s <= 0:
        raise ValueError("segment duration must be positive")
    propulsion_electrical_power_W = mechanical_power_W / propulsion_efficiency
    electrical_power_W = propulsion_electrical_power_W + auxiliary_power_W
    duration_h = duration_s / 3600.0
    return MissionSegmentResult(
        name=name,
        kind=kind,
        duration_min=duration_s / 60.0,
        horizontal_distance_km=distance_m / 1000.0,
        mechanical_energy_Wh=mechanical_power_W * duration_s / JOULES_PER_WH,
        electrical_energy_Wh=electrical_power_W * duration_h,
        average_electrical_power_W=electrical_power_W,
        assumptions=assumptions,
    )


def evaluate_mission_segments(
    definition: MissionDefinition,
    takeoff_mass_kg: float,
) -> tuple[MissionSegmentResult, ...]:
    _validate_mission_definition(definition)
    if takeoff_mass_kg <= 0:
        raise ValueError("takeoff mass must be positive")
    if definition.route_distance_km < definition.minimum_route_distance_km:
        raise ValueError(
            "route distance is shorter than the modeled climb and descent ground distance"
        )

    auxiliary_power_W = definition.auxiliary_power_kw * 1000.0
    taxi_duration_s = definition.taxi_duration_min * 60.0
    taxi_power_W = definition.taxi_propulsion_power_kw * 1000.0 + auxiliary_power_W
    taxi = MissionSegmentResult(
        name="Total taxi and ground operation",
        kind=SegmentKind.TAXI,
        duration_min=definition.taxi_duration_min,
        horizontal_distance_km=0.0,
        mechanical_energy_Wh=0.0,
        electrical_energy_Wh=taxi_power_W * taxi_duration_s / JOULES_PER_WH,
        average_electrical_power_W=taxi_power_W,
        assumptions="Direct electrical taxi and auxiliary load; no takeoff roll model.",
    )

    climb_duration_s = definition.climb_duration_s
    climb_distance_m = definition.climb_speed_m_per_s * climb_duration_s
    climb_drag_power_W = (
        _drag_force_n(takeoff_mass_kg, definition.climb_lift_to_drag_ratio)
        * definition.climb_speed_m_per_s
    )
    climb_potential_power_W = (
        takeoff_mass_kg * STANDARD_GRAVITY_M_S2 * definition.climb_rate_m_per_s
    )
    climb = _segment(
        name="Climb",
        kind=SegmentKind.CLIMB,
        duration_s=climb_duration_s,
        distance_m=climb_distance_m,
        mechanical_power_W=climb_drag_power_W + climb_potential_power_W,
        propulsion_efficiency=definition.propulsion_efficiency,
        auxiliary_power_W=auxiliary_power_W,
        assumptions="Constant speed/rate; drag plus gravitational potential energy.",
    )

    descent_duration_s = definition.descent_duration_s
    descent_distance_m = definition.descent_speed_m_per_s * descent_duration_s
    descent_level_drag_power_W = (
        _drag_force_n(takeoff_mass_kg, definition.descent_lift_to_drag_ratio)
        * definition.descent_speed_m_per_s
    )
    descent = _segment(
        name="Descent",
        kind=SegmentKind.DESCENT,
        duration_s=descent_duration_s,
        distance_m=descent_distance_m,
        mechanical_power_W=(
            descent_level_drag_power_W * definition.descent_propulsive_fraction
        ),
        propulsion_efficiency=definition.propulsion_efficiency,
        auxiliary_power_W=auxiliary_power_W,
        assumptions="No recovered potential energy; explicit fraction of level-drag power.",
    )

    cruise_distance_m = (
        definition.route_distance_km
        - climb.horizontal_distance_km
        - descent.horizontal_distance_km
    ) * 1000.0
    cruise_duration_s = cruise_distance_m / definition.cruise_speed_m_per_s
    cruise_drag_power_W = (
        _drag_force_n(takeoff_mass_kg, definition.cruise_lift_to_drag_ratio)
        * definition.cruise_speed_m_per_s
    )
    cruise = _segment(
        name="Cruise",
        kind=SegmentKind.CRUISE,
        duration_s=cruise_duration_s,
        distance_m=cruise_distance_m,
        mechanical_power_W=cruise_drag_power_W,
        propulsion_efficiency=definition.propulsion_efficiency,
        auxiliary_power_W=auxiliary_power_W,
        assumptions="Steady level flight at constant mass, speed, and lift-to-drag ratio.",
    )

    reserve_duration_s = definition.reserve_loiter_duration_min * 60.0
    reserve_distance_m = definition.reserve_speed_m_per_s * reserve_duration_s
    reserve_drag_power_W = (
        _drag_force_n(takeoff_mass_kg, definition.reserve_lift_to_drag_ratio)
        * definition.reserve_speed_m_per_s
    )
    if reserve_duration_s > 0:
        reserve = _segment(
            name="Reserve loiter",
            kind=SegmentKind.RESERVE,
            duration_s=reserve_duration_s,
            distance_m=reserve_distance_m,
            mechanical_power_W=reserve_drag_power_W,
            propulsion_efficiency=definition.propulsion_efficiency,
            auxiliary_power_W=auxiliary_power_W,
            assumptions="Explicit steady-level loiter reserve; no regulatory claim.",
        )
    else:
        reserve = MissionSegmentResult(
            name="Reserve loiter",
            kind=SegmentKind.RESERVE,
            duration_min=0.0,
            horizontal_distance_km=0.0,
            mechanical_energy_Wh=0.0,
            electrical_energy_Wh=0.0,
            average_electrical_power_W=0.0,
            assumptions="No reserve duration configured; no regulatory claim.",
        )
    return taxi, climb, cruise, reserve, descent


def solve_battery_mass_closure(
    definition: MissionDefinition,
    *,
    tolerance_fraction: float = 1e-7,
    maximum_iterations: int = 200,
    damping: float = 0.5,
) -> MissionSolution:
    _validate_mission_definition(definition)
    if not 0 < tolerance_fraction < 1:
        raise ValueError("tolerance_fraction must be in (0, 1)")
    if maximum_iterations <= 0:
        raise ValueError("maximum_iterations must be positive")
    if not 0 < damping <= 1:
        raise ValueError("damping must be in (0, 1]")

    battery_mass_kg = 0.0
    segments: tuple[MissionSegmentResult, ...] = ()
    energy_mass = power_mass = c_rate_mass = 0.0
    required_mass = 0.0
    converged = False
    divergence_limit_kg = definition.maximum_takeoff_mass_kg * 100.0

    for iteration in range(1, maximum_iterations + 1):
        takeoff_mass_kg = definition.fixed_mass_kg + battery_mass_kg
        try:
            segments = evaluate_mission_segments(definition, takeoff_mass_kg)
        except ValueError as exc:
            return MissionSolution(
                definition=definition,
                converged=False,
                feasible=False,
                iterations=iteration,
                battery_mass_kg=battery_mass_kg,
                takeoff_mass_kg=takeoff_mass_kg,
                battery_mass_fraction=(
                    battery_mass_kg / takeoff_mass_kg if takeoff_mass_kg else 0.0
                ),
                terminal_electrical_energy_Wh=0.0,
                nominal_battery_energy_Wh=0.0,
                peak_electrical_power_W=0.0,
                energy_limited_mass_kg=0.0,
                specific_power_limited_mass_kg=0.0,
                c_rate_limited_mass_kg=0.0,
                limiting_constraint="invalid_profile",
                segments=(),
                reasons=(str(exc),),
            )

        terminal_energy_Wh = sum(segment.electrical_energy_Wh for segment in segments)
        nominal_energy_Wh = terminal_energy_Wh / definition.energy_availability_fraction
        peak_power_W = (
            max(segment.average_electrical_power_W for segment in segments)
            * (1 + definition.peak_power_margin_fraction)
        )
        energy_mass = nominal_energy_Wh / definition.pack_specific_energy_Wh_kg
        power_mass = peak_power_W / (
            definition.pack_specific_power_W_kg
            * definition.power_availability_fraction
        )
        c_rate_mass = peak_power_W / (
            definition.pack_specific_energy_Wh_kg
            * definition.maximum_continuous_c_rate
            * definition.power_availability_fraction
        )
        required_mass = max(energy_mass, power_mass, c_rate_mass)
        if required_mass > divergence_limit_kg:
            break

        scale = max(required_mass, 1.0)
        if abs(required_mass - battery_mass_kg) / scale <= tolerance_fraction:
            battery_mass_kg = required_mass
            converged = True
            break
        battery_mass_kg = (1 - damping) * battery_mass_kg + damping * required_mass

    takeoff_mass_kg = definition.fixed_mass_kg + battery_mass_kg
    battery_fraction = battery_mass_kg / takeoff_mass_kg
    terminal_energy_Wh = sum(segment.electrical_energy_Wh for segment in segments)
    nominal_energy_Wh = (
        terminal_energy_Wh / definition.energy_availability_fraction
        if segments
        else 0.0
    )
    peak_power_W = (
        max(segment.average_electrical_power_W for segment in segments)
        * (1 + definition.peak_power_margin_fraction)
        if segments
        else 0.0
    )
    constraints = {
        "energy": energy_mass,
        "specific_power": power_mass,
        "c_rate": c_rate_mass,
    }
    limiting_constraint = max(constraints, key=constraints.get)
    reasons: list[str] = []
    if not converged:
        reasons.append(
            "battery-mass closure did not converge; energy-mass feedback may be divergent"
        )
    if takeoff_mass_kg > definition.maximum_takeoff_mass_kg:
        reasons.append("required takeoff mass exceeds the configured maximum")
    structural_battery_fraction = (
        battery_mass_kg / definition.maximum_takeoff_mass_kg
    )
    if structural_battery_fraction > definition.maximum_battery_mass_fraction:
        reasons.append("required battery fraction exceeds the configured maximum")
    return MissionSolution(
        definition=definition,
        converged=converged,
        feasible=not reasons,
        iterations=iteration,
        battery_mass_kg=battery_mass_kg,
        takeoff_mass_kg=takeoff_mass_kg,
        battery_mass_fraction=battery_fraction,
        terminal_electrical_energy_Wh=terminal_energy_Wh,
        nominal_battery_energy_Wh=nominal_energy_Wh,
        peak_electrical_power_W=peak_power_W,
        energy_limited_mass_kg=energy_mass,
        specific_power_limited_mass_kg=power_mass,
        c_rate_limited_mass_kg=c_rate_mass,
        limiting_constraint=limiting_constraint,
        segments=segments,
        reasons=tuple(reasons),
    )


def maximum_feasible_range_km(
    definition: MissionDefinition,
    *,
    iterations: int = 50,
) -> float:
    minimum_distance = definition.minimum_route_distance_km * (1 + 1e-9)
    minimum_case = replace(definition, route_distance_km=minimum_distance)
    if not solve_battery_mass_closure(minimum_case).feasible:
        return 0.0

    upper_case = replace(
        definition,
        route_distance_km=definition.range_search_upper_km,
    )
    if solve_battery_mass_closure(upper_case).feasible:
        return definition.range_search_upper_km

    lower = minimum_distance
    upper = definition.range_search_upper_km
    for _ in range(iterations):
        midpoint = (lower + upper) / 2
        candidate = replace(definition, route_distance_km=midpoint)
        if solve_battery_mass_closure(candidate).feasible:
            lower = midpoint
        else:
            upper = midpoint
    return lower


def payload_range_curve(
    definition: MissionDefinition,
    *,
    points: int = 6,
) -> list[dict[str, float]]:
    if points < 2:
        raise ValueError("points must be at least 2")
    output = []
    for index in range(points):
        payload_kg = definition.maximum_payload_kg * index / (points - 1)
        candidate = replace(definition, payload_mass_kg=payload_kg)
        output.append(
            {
                "payload_kg": payload_kg,
                "maximum_range_km": maximum_feasible_range_km(candidate),
            }
        )
    return output


def mission_sensitivity(definition: MissionDefinition) -> list[dict[str, object]]:
    cases = [
        ("pack specific energy -20%", {"pack_specific_energy_Wh_kg": 0.8}),
        ("pack specific energy +20%", {"pack_specific_energy_Wh_kg": 1.2}),
        ("cruise lift-to-drag -10%", {"cruise_lift_to_drag_ratio": 0.9}),
        ("cruise lift-to-drag +10%", {"cruise_lift_to_drag_ratio": 1.1}),
        ("propulsion efficiency -5%", {"propulsion_efficiency": 0.95}),
        ("propulsion efficiency +5%", {"propulsion_efficiency": 1.05}),
        ("reserve duration -50%", {"reserve_loiter_duration_min": 0.5}),
        ("reserve duration +50%", {"reserve_loiter_duration_min": 1.5}),
    ]
    baseline = solve_battery_mass_closure(definition)
    rows: list[dict[str, object]] = [
        {
            "case": "baseline",
            "feasible": baseline.feasible,
            "converged": baseline.converged,
            "battery_mass_kg": baseline.battery_mass_kg,
            "change_from_baseline_fraction": 0.0 if baseline.converged else None,
            "comparison_valid": baseline.converged,
        }
    ]
    for label, changes in cases:
        field, factor = next(iter(changes.items()))
        current = getattr(definition, field)
        value = current * factor
        if field == "propulsion_efficiency":
            value = min(value, 1.0)
        solution = solve_battery_mass_closure(replace(definition, **{field: value}))
        comparison_valid = baseline.converged and solution.converged
        change = (
            (solution.battery_mass_kg / baseline.battery_mass_kg) - 1
            if comparison_valid and baseline.battery_mass_kg > 0
            else None
        )
        rows.append(
            {
                "case": label,
                "feasible": solution.feasible,
                "converged": solution.converged,
                "battery_mass_kg": solution.battery_mass_kg,
                "change_from_baseline_fraction": change,
                "comparison_valid": comparison_valid,
            }
        )
    return rows
