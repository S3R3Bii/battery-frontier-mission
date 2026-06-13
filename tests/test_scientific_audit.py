from battery_frontier.scientific_audit import (
    REQUIRED_RANKING_FIELDS,
    evaluate_ranking_gate,
)


def test_empty_candidate_set_cannot_be_ranked() -> None:
    gate = evaluate_ranking_gate([])
    assert gate.allowed is False


def test_missing_uncertainty_blocks_ranking() -> None:
    candidate = {field: "present" for field in REQUIRED_RANKING_FIELDS}
    candidate["id"] = "candidate.test"
    candidate["pack_specific_energy_uncertainty"] = None
    gate = evaluate_ranking_gate([candidate])
    assert gate.allowed is False
    assert "pack_specific_energy_uncertainty" in gate.missing_by_candidate["candidate.test"]


def test_complete_minimum_contract_passes_first_gate() -> None:
    candidate = {field: "present" for field in REQUIRED_RANKING_FIELDS}
    candidate["id"] = "candidate.test"
    gate = evaluate_ranking_gate([candidate])
    assert gate.allowed is True

