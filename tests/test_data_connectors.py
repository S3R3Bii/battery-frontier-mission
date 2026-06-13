import json

from battery_frontier.data.connectors import (
    dry_run_source,
    source_status_rows,
    write_snapshot_manifest,
)
from battery_frontier.registry import load_registries


def test_source_status_preserves_license_gates(monkeypatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)
    registries = load_registries()
    rows = source_status_rows(registries)
    by_id = {row["source_id"]: row for row in rows}

    assert by_id["datasource.materials_project"]["requires_key"] is True
    assert by_id["datasource.materials_project"]["credential_available"] is False
    assert all(row["trusted_publication_allowed"] is False for row in rows)


def test_materials_project_dry_run_reports_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("MP_API_KEY", raising=False)
    registries = load_registries()
    result = dry_run_source(
        registries,
        "datasource.materials_project",
        query="Li-S cathode",
    )

    assert result["status"] == "blocked_requires_key"
    assert result["trusted_publication"] is False
    assert result["ranking_evidence"] is False


def test_api_failure_manifest_is_not_trusted(monkeypatch, tmp_path) -> None:
    registries = load_registries()

    from battery_frontier.data import connectors

    connector = connectors.CONNECTORS["datasource.nasa_ntrs"]

    def fail_fetch(query: str, rows: int):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(connector, "fetch", fail_fetch)
    result = dry_run_source(
        registries,
        "datasource.nasa_ntrs",
        query="electric aircraft battery",
        execute=True,
    )
    manifest_path = write_snapshot_manifest(result, output_dir=tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert result["status"] == "api_error"
    assert manifest["trusted_publication"] is False
    assert manifest["ranking_evidence"] is False
    assert manifest["row_count"] == 0
