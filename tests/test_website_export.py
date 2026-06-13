import json

from battery_frontier.website import export_website_data


def test_website_export_contains_frontier_and_guardrails(tmp_path) -> None:
    path = export_website_data(output_path=tmp_path / "mission-control-data.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["phase"] == "4"
    assert payload["technology_readiness_claim"] is False
    assert payload["ranking_enabled"] is False
    assert payload["audited_measurements"] == 0
    assert payload["frontier"]["mission_bands"]
    assert payload["frontier"]["points"][0]["specific_energy_Wh_kg"] is None
    assert "audited-measurement lane is empty" in payload["frontier"]["unknown_region_note"]
    assert payload["candidate_dossier_summary"]["candidate_count"] > 0
    assert payload["candidate_dossier_summary"]["ranking_enabled"] is False
    assert payload["materials_project_appendix"]["ranking_evidence"] is False
    assert payload["conceptual_target_system"]["claim_boundary"].startswith("Speculative")
    assert payload["simulation_campaign_summary"]["simulation_only"] is True
    assert payload["simulation_campaign_summary"]["ranking_enabled"] is False
    assert payload["simulation_campaign_summary"]["audited_measurements"] == 0
    assert payload["aviation_requirement_map"]["row_count"] > 0
    assert payload["pack_trade_space_summary"]["row_count"] > 0
    assert payload["candidate_envelopes"]
    assert payload["what_would_need_to_be_true"]
    assert any(
        candidate["id"] == "candidate.hemp_bast_graphitic_carbon"
        for candidate in payload["candidate_dossiers"]
    )
