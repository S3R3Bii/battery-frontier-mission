from battery_frontier.candidates.dossiers import (
    build_candidate_dossiers,
    build_materials_project_appendix,
)
from battery_frontier.registry import load_registries


def test_candidate_dossiers_include_hemp_without_ranking(monkeypatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)
    payload = build_candidate_dossiers(execute_materials_project=False)
    by_id = {candidate["id"]: candidate for candidate in payload["dossiers"]}
    hemp = by_id["candidate.hemp_bast_graphitic_carbon"]

    assert payload["ranking_enabled"] is False
    assert hemp["ranking_allowed"] is False
    assert hemp["audited_measurement_count"] == 0
    assert hemp["performance_evidence"] is False
    assert "pack_specific_energy_uncertainty" in hemp["ranking_blockers"]
    assert "speculative" in hemp["evidence_status"]
    assert "validated graphene" in " ".join(hemp["notes"])


def test_materials_project_appendix_is_metadata_only_and_redacted(monkeypatch) -> None:
    monkeypatch.setenv("MP_API_KEY", "test-key")
    appendix = build_materials_project_appendix(
        load_registries(),
        execute_if_available=False,
    )
    serialized = str(appendix)

    assert appendix["metadata_only"] is True
    assert appendix["ranking_evidence"] is False
    assert appendix["performance_evidence"] is False
    assert "test-key" not in serialized
    assert "<env:MP_API_KEY>" in serialized


def test_fixture_and_metadata_do_not_appear_as_audited_measurements(monkeypatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)
    payload = build_candidate_dossiers(execute_materials_project=False)

    assert payload["audited_measurements"] == 0
    assert payload["summary"]["audited_measurement_count"] == 0
    assert all(candidate["audited_measurement_count"] == 0 for candidate in payload["dossiers"])
    assert all(candidate["performance_evidence"] is False for candidate in payload["dossiers"])
    assert payload["materials_project_appendix"]["performance_evidence"] is False


def test_candidate_dossier_summarizes_materials_project_status(monkeypatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)
    payload = build_candidate_dossiers(execute_materials_project=False)
    summary = payload["summary"]["materials_project_appendix"]

    assert summary["query_count"] > 0
    assert summary["ranking_evidence"] is False
    assert summary["performance_evidence"] is False
    assert "blocked_requires_key" in summary["status_counts"]
