import json
from dataclasses import replace

import pytest

from battery_frontier import __version__
from battery_frontier.aviation.reference_cases import (
    calculate_all_mission_cases,
    write_mission_results,
)
from battery_frontier.aviation.segmented import (
    mission_definition_from_case,
    mission_sensitivity,
    payload_range_curve,
    solve_battery_mass_closure,
)
from battery_frontier.registry import load_registries


def _mission_cases():
    registries = load_registries()
    return {case.id: case for case in registries.segmented_mission_cases}


def test_regional_case_closes_with_explicit_segments() -> None:
    case = _mission_cases()["mission.regional_demonstrator"]
    solution = solve_battery_mass_closure(mission_definition_from_case(case))

    assert solution.converged is True
    assert solution.feasible is True
    assert solution.takeoff_mass_kg <= case.maximum_takeoff_mass_kg
    assert solution.limiting_constraint == "energy"
    assert [segment.kind.value for segment in solution.segments] == [
        "taxi",
        "climb",
        "cruise",
        "reserve",
        "descent",
    ]
    assert sum(segment.electrical_energy_Wh for segment in solution.segments) == (
        pytest.approx(solution.terminal_electrical_energy_Wh)
    )


def test_long_range_stress_case_reports_divergence() -> None:
    case = _mission_cases()["mission.single_aisle_stress"]
    solution = solve_battery_mass_closure(mission_definition_from_case(case))

    assert solution.converged is False
    assert solution.feasible is False
    assert any("did not converge" in reason for reason in solution.reasons)
    assert any("takeoff mass" in reason for reason in solution.reasons)


def test_payload_range_decreases_as_payload_increases() -> None:
    case = _mission_cases()["mission.regional_demonstrator"]
    curve = payload_range_curve(mission_definition_from_case(case), points=6)
    ranges = [point["maximum_range_km"] for point in curve]

    assert ranges == sorted(ranges, reverse=True)
    assert ranges[0] > ranges[-1] > 0


def test_sensitivity_preserves_visible_baseline() -> None:
    case = _mission_cases()["mission.regional_demonstrator"]
    rows = mission_sensitivity(mission_definition_from_case(case))
    by_name = {row["case"]: row for row in rows}

    assert by_name["baseline"]["feasible"] is True
    assert by_name["baseline"]["comparison_valid"] is True
    assert by_name["pack specific energy +20%"]["battery_mass_kg"] < (
        by_name["baseline"]["battery_mass_kg"]
    )
    assert by_name["reserve duration +50%"]["battery_mass_kg"] > (
        by_name["baseline"]["battery_mass_kg"]
    )


def test_divergent_sensitivity_does_not_report_percentage_precision() -> None:
    case = _mission_cases()["mission.single_aisle_stress"]
    rows = mission_sensitivity(mission_definition_from_case(case))

    assert all(row["comparison_valid"] is False for row in rows)
    assert all(row["change_from_baseline_fraction"] is None for row in rows)


def test_power_and_c_rate_can_independently_limit_battery_mass() -> None:
    case = _mission_cases()["mission.regional_demonstrator"]
    definition = mission_definition_from_case(case)

    power_limited = solve_battery_mass_closure(
        replace(
            definition,
            pack_specific_power_W_kg=50,
            maximum_continuous_c_rate=100,
        )
    )
    c_rate_limited = solve_battery_mass_closure(
        replace(
            definition,
            pack_specific_power_W_kg=10_000,
            maximum_continuous_c_rate=0.05,
        )
    )

    assert power_limited.limiting_constraint == "specific_power"
    assert c_rate_limited.limiting_constraint == "c_rate"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("route_distance_km", 0),
        ("pack_specific_energy_Wh_kg", 0),
        ("reserve_loiter_duration_min", 0),
        ("maximum_continuous_c_rate", -1),
    ],
)
def test_segmented_mission_rejects_nonphysical_direct_inputs(
    field: str,
    value: float,
) -> None:
    case = _mission_cases()["mission.regional_demonstrator"]
    definition = mission_definition_from_case(case)

    with pytest.raises(ValueError):
        solve_battery_mass_closure(replace(definition, **{field: value}))


def test_registered_mission_cases_have_feasible_and_failure_examples() -> None:
    registries = load_registries()
    results = calculate_all_mission_cases(registries.segmented_mission_cases)
    by_id = {result["id"]: result for result in results}

    assert by_id["mission.regional_demonstrator"]["feasible"] is True
    assert by_id["mission.single_aisle_stress"]["feasible"] is False


def test_aviation_artifact_contains_provenance(tmp_path) -> None:
    registries = load_registries()
    path = write_mission_results(
        registries.segmented_mission_cases,
        output_path=tmp_path / "aviation.json",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["package_version"] == __version__
    assert payload["config_sha256"]
    assert payload["code_snapshot_sha256"]
    assert payload["code_hashes"]
    assert len(payload["cases"]) == 2
