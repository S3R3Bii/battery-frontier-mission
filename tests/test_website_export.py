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
