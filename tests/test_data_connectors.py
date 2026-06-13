import json
from urllib.parse import parse_qs, urlparse

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
    assert by_id["datasource.cmu_evtol_battery"]["trusted_publication_allowed"] is True
    assert by_id["datasource.cmu_evtol_battery"]["metadata_only"] is True
    assert all(
        row["trusted_publication_allowed"] is False
        for row in rows
        if row["source_id"] != "datasource.cmu_evtol_battery"
    )


def test_cmu_evtol_dry_run_builds_figshare_request() -> None:
    registries = load_registries()
    result = dry_run_source(
        registries,
        "datasource.cmu_evtol_battery",
        query="14226830",
        rows=3,
    )

    assert result["status"] == "dry_run"
    assert result["trusted_publication"] is False
    assert result["license_status"] == "approved"
    assert result["execution_supported"] is True
    assert result["request"]["url"] == "https://api.figshare.com/v2/articles/14226830"
    assert result["ranking_evidence"] is False


def test_cmu_evtol_execute_normalizes_file_metadata(monkeypatch) -> None:
    registries = load_registries()

    from battery_frontier.data import connectors

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(
                {
                    "id": 14226830,
                    "title": "eVTOL Battery Dataset",
                    "doi": "10.1184/R1/14226830",
                    "url_public_html": (
                        "https://kilthub.cmu.edu/articles/dataset/"
                        "eVTOL_Battery_Dataset/14226830"
                    ),
                    "version": 3,
                    "published_date": "2023-04-21T18:33:00Z",
                    "license": {
                        "name": "CC BY 4.0",
                        "url": "https://creativecommons.org/licenses/by/4.0/",
                    },
                    "files": [
                        {
                            "id": 1,
                            "name": "VAH01.csv",
                            "size": 123,
                            "download_url": "https://figshare.com/file/download/1",
                            "supplied_md5": "abc123",
                        }
                    ],
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == connectors.FETCH_TIMEOUT_S
        assert request.full_url == "https://api.figshare.com/v2/articles/14226830"
        return FakeResponse()

    monkeypatch.setattr(connectors, "urlopen", fake_urlopen)

    result = dry_run_source(
        registries,
        "datasource.cmu_evtol_battery",
        query="14226830",
        rows=5,
        execute=True,
    )

    assert result["status"] == "fetched"
    assert result["trusted_publication"] is True
    assert result["ranking_evidence"] is False
    assert result["record_count"] == 1
    record = result["records"][0]
    assert record["record_type"] == "approved_experimental_dataset_file_metadata"
    assert record["metadata_only"] is True
    assert record["performance_evidence"] is False
    assert record["ranking_evidence"] is False
    assert record["system_boundary"].startswith("cell-level experimental")
    assert record["file_name"] == "VAH01.csv"


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


def test_materials_project_dry_run_builds_redacted_request(monkeypatch) -> None:
    monkeypatch.setenv("MP_API_KEY", "test-key")
    registries = load_registries()
    result = dry_run_source(
        registries,
        "datasource.materials_project",
        query="Li-S cathode",
        rows=3,
    )
    parsed = urlparse(result["request"]["url"])
    params = parse_qs(parsed.query)

    assert result["status"] == "dry_run"
    assert result["credential_available"] is True
    assert result["execution_supported"] is True
    assert result["request"]["headers"]["X-API-KEY"] == "<env:MP_API_KEY>"
    assert params["elements"] == ["Li,S"]
    assert params["_limit"] == ["3"]
    assert "material_id" in params["_fields"][0]


def test_materials_project_execute_normalizes_metadata(monkeypatch) -> None:
    monkeypatch.setenv("MP_API_KEY", "test-key")
    registries = load_registries()

    from battery_frontier.data import connectors

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(
                {
                    "data": [
                        {
                            "material_id": "mp-1",
                            "formula_pretty": "Li2O",
                            "chemsys": "Li-O",
                            "elements": ["Li", "O"],
                            "density": 2.0,
                            "energy_above_hull": 0.0,
                            "formation_energy_per_atom": -2.1,
                            "is_stable": True,
                            "theoretical": False,
                            "last_updated": "2026-01-01T00:00:00Z",
                        }
                    ],
                    "meta": {"total_doc": 1},
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == connectors.FETCH_TIMEOUT_S
        assert request.headers["X-api-key"] == "test-key"
        return FakeResponse()

    monkeypatch.setattr(connectors, "urlopen", fake_urlopen)

    result = dry_run_source(
        registries,
        "datasource.materials_project",
        query="Li-O",
        rows=1,
        execute=True,
    )

    assert result["status"] == "fetched"
    assert result["executed"] is True
    assert result["trusted_publication"] is False
    assert result["ranking_evidence"] is False
    assert result["record_count"] == 1
    assert result["request"]["headers"]["X-API-KEY"] == "<env:MP_API_KEY>"
    assert result["records"][0]["record_type"] == "computed_material_metadata"
    assert result["records"][0]["performance_evidence"] is False


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
