import pytest
from pydantic import ValidationError

from battery_frontier.materials.campaign import build_materials_campaign
from battery_frontier.schemas import EvidenceClass, MaterialCandidate


@pytest.fixture(autouse=True)
def _disable_materials_project_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)


def _candidate_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "material.test_candidate",
        "material_id": "material.test_candidate",
        "display_name": "Test candidate",
        "chemistry_family_id": "chemistry.lithium_ion_intercalation",
        "chemistry_family": "Advanced lithium-ion intercalation",
        "role": "cell_system",
        "evidence_level": EvidenceClass.SPECULATIVE_HYPOTHESIS,
        "source_type": "unit_test",
        "system_boundary": "Unit-test full-cell hypothesis boundary only.",
        "theoretical_basis": "Unit-test theoretical basis with explicit assumptions.",
        "measured_basis": None,
        "aviation_relevance": "Unit-test relevance for aviation gap screening only.",
        "key_limitations": ["unit_test_limitation"],
        "toxicity_safety_flags": ["unit_test_safety_review"],
        "abundance_supply_flags": ["unit_test_supply_review"],
        "manufacturability_flags": ["unit_test_manufacturing_review"],
        "theoretical_specific_capacity_mAh_g": 100.0,
        "nominal_voltage_v": 3.0,
        "nominal_voltage_note": "Unit-test voltage assumption.",
        "cell_derating_factor": 0.5,
        "pack_overhead_factor": 0.7,
        "citation_ids": [],
        "source_urls": ["https://example.com/material"],
        "may_appear_in_audited_lane": False,
    }
    payload.update(overrides)
    return payload


def test_material_hypotheses_cannot_be_audited_measurements() -> None:
    payload = build_materials_campaign()

    assert payload["summary"]["ranking_enabled"] is False
    assert payload["summary"]["audited_measurements"] == 0
    assert all(not card["audited_measurement"] for card in payload["material_candidate_cards"])
    assert all(not card["performance_evidence"] for card in payload["material_candidate_cards"])
    assert all(not card["ranking_evidence"] for card in payload["material_candidate_cards"])


def test_hemp_bast_fiber_carbon_is_exploratory_only() -> None:
    payload = build_materials_campaign()
    hemp = next(
        card
        for card in payload["material_candidate_cards"]
        if card["material_id"] == "material.hemp_bast_fiber_graphene_like_carbon"
    )

    assert hemp["energy_estimate_status"] == "blocked_missing_capacity_and_voltage"
    assert hemp["engineering_bounded_pack_Wh_kg"] is None
    assert hemp["may_appear_in_audited_lane"] is False
    assert "Exploratory carbon architecture" in hemp["hemp_bast_fiber_guardrail"]


def test_materials_project_metadata_is_not_performance_evidence() -> None:
    payload = build_materials_campaign()
    snapshot = payload["materials_project_metadata"]

    assert snapshot["metadata_only"] is True
    assert snapshot["performance_evidence"] is False
    assert snapshot["ranking_evidence"] is False
    assert snapshot["audited_measurement"] is False


def test_missing_voltage_or_capacity_blocks_energy_estimate() -> None:
    payload = build_materials_campaign()
    by_id = {card["material_id"]: card for card in payload["material_candidate_cards"]}

    lithium_metal = by_id["material.lithium_metal_anode"]
    structural = by_id["material.structural_battery_composite"]

    assert lithium_metal["energy_estimate_status"] == "blocked_missing_voltage"
    assert lithium_metal["engineering_bounded_pack_Wh_kg"] is None
    assert structural["energy_estimate_status"] == "blocked_missing_capacity_and_voltage"
    assert structural["engineering_bounded_pack_Wh_kg"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("theoretical_specific_capacity_mAh_g", 0.0),
        ("theoretical_specific_capacity_mAh_g", -1.0),
        ("nominal_voltage_v", 0.0),
        ("nominal_voltage_v", -1.0),
        ("cell_derating_factor", 0.0),
        ("pack_overhead_factor", -0.2),
    ],
)
def test_invalid_material_screening_numbers_are_rejected(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValidationError):
        MaterialCandidate.model_validate(_candidate_payload(**{field: value}))


def test_audited_lane_flag_requires_measured_basis() -> None:
    with pytest.raises(ValidationError):
        MaterialCandidate.model_validate(
            _candidate_payload(may_appear_in_audited_lane=True)
        )


def test_material_frontier_gap_rows_are_diagnostics_only() -> None:
    payload = build_materials_campaign()

    assert payload["material_frontier_gap"]
    assert all(not row["audited_measurement"] for row in payload["material_frontier_gap"])
    assert all(not row["performance_evidence"] for row in payload["material_frontier_gap"])
    assert all(not row["ranking_evidence"] for row in payload["material_frontier_gap"])
    assert any(
        row["mission_profile_id"] == "mission.long_haul_6000km_stress"
        and row["diagnostic_status"] in {"gap_remaining", "not_energy_estimated"}
        for row in payload["material_frontier_gap"]
    )
