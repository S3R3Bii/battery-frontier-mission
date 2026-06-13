import json

import pytest

from battery_frontier.registry import load_registries
from battery_frontier.simulations.campaign import (
    build_aviation_requirement_grid,
    build_simulation_campaign,
    validate_sweep_parameters,
    verify_simulation_artifacts,
    write_simulation_campaign,
)


def test_simulation_campaign_artifacts_are_generated(tmp_path) -> None:
    summary_path, markdown_path, artifacts = write_simulation_campaign(output_dir=tmp_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    aviation = json.loads(artifacts["aviation_json"].read_text(encoding="utf-8"))
    pack = json.loads(artifacts["pack_json"].read_text(encoding="utf-8"))

    assert markdown_path.exists()
    assert summary["summary"]["aviation_requirement_grid_rows"] == aviation["row_count"]
    assert summary["summary"]["pack_trade_space_rows"] == pack["row_count"]
    assert summary["summary"]["candidate_envelope_count"] == 11
    assert summary["summary"]["ranking_enabled"] is False
    assert summary["summary"]["audited_measurements"] == 0
    assert all(row["hash_matches"] for row in verify_simulation_artifacts(summary_path))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("route_distance_km", 0),
        ("aircraft_mass_kg", -1),
        ("pack_specific_energy_Wh_kg", 0),
        ("pack_specific_power_W_kg", 0),
        ("maximum_continuous_c_rate", -0.1),
        ("reserve_duration_min", 0),
        ("voltage_V", 0),
        ("propulsion_efficiency", 1.2),
        ("thermal_availability", 0),
        ("maximum_battery_mass_fraction", 1),
    ],
)
def test_simulation_sweep_rejects_nonphysical_inputs(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        validate_sweep_parameters(**{field: value})


def test_impossible_mission_conditions_are_explicitly_infeasible() -> None:
    rows = build_aviation_requirement_grid(load_registries())
    infeasible = [row for row in rows if not row["feasible"]]

    assert infeasible
    assert all(row["limiting_constraint"] for row in infeasible)
    assert any("required takeoff mass" in row["infeasibility_reasons"] for row in infeasible)


def test_simulation_outputs_never_become_audited_measurements() -> None:
    payload = build_simulation_campaign()

    assert payload["summary"]["audited_measurements"] == 0
    assert payload["summary"]["ranking_enabled"] is False
    assert all(row["audited_measurement"] is False for row in payload["aviation_requirement_grid"])
    assert all(row["performance_evidence"] is False for row in payload["pack_trade_space"])
    assert all(
        row["audited_measurement_count"] == 0 for row in payload["candidate_envelopes"]
    )


def test_candidate_envelopes_keep_hemp_speculative_and_unranked() -> None:
    payload = build_simulation_campaign()
    by_id = {row["candidate_id"]: row for row in payload["candidate_envelopes"]}
    hemp = by_id["candidate.hemp_bast_graphitic_carbon"]

    assert hemp["ranking_allowed"] is False
    assert hemp["performance_evidence"] is False
    assert "not validated graphene" in hemp["hemp_specific_guardrail"]
    assert all(
        envelope["full_cell_specific_energy_Wh_kg"] is None
        for envelope in hemp["envelopes"]
    )


def test_stale_simulation_artifact_hash_fails_verification(tmp_path) -> None:
    summary_path, _, artifacts = write_simulation_campaign(output_dir=tmp_path)
    artifacts["aviation_csv"].write_text("tampered\n", encoding="utf-8")
    rows = verify_simulation_artifacts(summary_path)
    by_id = {row["artifact_id"]: row for row in rows}

    assert by_id["aviation_requirement_grid_csv"]["hash_matches"] is False
