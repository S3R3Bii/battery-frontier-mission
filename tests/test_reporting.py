import json
from datetime import date

from battery_frontier.reporting.daily import generate_daily_report


def test_daily_report_records_provenance_and_disables_ranking(tmp_path) -> None:
    report_path, manifest_path = generate_daily_report(
        report_date=date(2026, 6, 12),
        output_dir=tmp_path,
    )
    report = report_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "Chemistry performance ranking is intentionally disabled" in report
    assert manifest["ranking_enabled"] is False
    assert manifest["config_hashes"]
    assert manifest["code_hashes"]
    assert manifest["code_snapshot_sha256"]
    assert manifest["report_sha256"]
    assert manifest["summary_sha256"]
    assert manifest["summary_path"]
    assert manifest["dashboard_artifacts"] == 4
    assert manifest["dashboard_manifest_sha256"]
    assert manifest["candidate_dossiers"] > 0
    assert manifest["simulation_campaign_rows"]["aviation_requirement_grid"] > 0
    assert manifest["simulation_campaign_rows"]["long_haul_feasibility"] == 6
    assert manifest["simulation_campaign_sha256"]
    assert manifest["experimental_measurements"] >= 0
    assert manifest["cmu_measurement_summary_sha256"]
    assert manifest["partner_dossier_count"] == 5

    summary_path = tmp_path / "2026-06-12-mission-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["ranking_enabled"] is False
    assert summary["audited_measurements"] >= 0
    assert summary["measurement_quality_status"] in {"passed", "blocked", "not_parsed"}
    assert summary["cmu_measurement_summary_sha256"]
    assert summary["connector_readiness"]
    assert summary["candidate_dossiers"] > 0
    assert summary["partner_dossier_count"] == 5
    assert summary["candidate_summary"]["ranking_enabled"] is False
    assert summary["simulation_campaign"]["simulation_only"] is True
    assert summary["simulation_campaign"]["ranking_enabled"] is False
