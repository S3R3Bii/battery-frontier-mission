import hashlib
import io
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from battery_frontier.measurements import cmu_evtol
from battery_frontier.measurements.cmu_evtol import (
    MeasurementQualityError,
    build_measurement_summary,
    download_cmu_evtol_files,
    parse_timeseries_csv,
    verify_raw_snapshot,
)


def _csv_text(time_value: float = 0.0, voltage: float = 3.7, temperature: float = 25.0) -> str:
    return "\n".join(
        [
            "time_s,Ecell_V,I_mA,EnergyCharge_W_h,QCharge_mA_h,"
            "EnergyDischarge_W_h,QDischarge_mA_h,Temperature__C,cycleNumber,Ns",
            f"{time_value},{voltage},100,0.1,10,0,0,{temperature},0,1",
            f"{time_value + 1},{voltage},-100,0.1,10,-0.2,20,{temperature + 1},0,2",
            "",
        ]
    )


def _source_manifest(path: Path, content: bytes) -> Path:
    digest = hashlib.md5(content, usedforsecurity=False).hexdigest()
    payload = {
        "result": {
            "records": [
                {
                    "file_id": 1,
                    "file_name": "fixture.csv",
                    "file_size_bytes": len(content),
                    "download_url": "https://example.test/fixture.csv",
                    "supplied_md5": digest,
                    "license": "CC BY 4.0",
                    "published_date": "2026-01-01T00:00:00Z",
                    "modified_date": "2026-01-01T00:00:00Z",
                }
            ]
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False


def test_cmu_subset_downloader_writes_hash_manifest(tmp_path, monkeypatch) -> None:
    content = _csv_text().encode("utf-8")
    source_manifest = _source_manifest(tmp_path / "source.json", content)

    def fake_urlopen(*args, **kwargs):
        return _FakeResponse(content)

    monkeypatch.setattr(cmu_evtol, "urlopen", fake_urlopen)
    manifest = download_cmu_evtol_files(
        mode="all",
        raw_dir=tmp_path / "raw",
        source_manifest_path=source_manifest,
        output_dir=tmp_path / "reports",
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))

    assert payload["downloaded_size_bytes"] == len(content)
    assert payload["records"][0]["md5_matches"] is True
    assert payload["records"][0]["computed_sha256"]
    assert payload["records"][0]["pack_level_evidence"] is False
    assert payload["records"][0]["candidate_ranking_evidence"] is False


def test_cmu_download_failure_removes_partial_file(tmp_path, monkeypatch) -> None:
    content = _csv_text().encode("utf-8")
    source_manifest = _source_manifest(tmp_path / "source.json", content)

    def fake_urlopen(*args, **kwargs):
        raise URLError("network unavailable")

    monkeypatch.setattr(cmu_evtol, "urlopen", fake_urlopen)
    with pytest.raises(cmu_evtol.CmuEvtolIngestionError):
        download_cmu_evtol_files(
            mode="all",
            raw_dir=tmp_path / "raw",
            source_manifest_path=source_manifest,
            output_dir=tmp_path / "reports",
        )

    assert not (tmp_path / "raw" / "fixture.csv").exists()
    assert not (tmp_path / "raw" / "fixture.csv.part").exists()


def test_raw_manifest_hash_verification_fails_after_tamper(tmp_path, monkeypatch) -> None:
    content = _csv_text().encode("utf-8")
    source_manifest = _source_manifest(tmp_path / "source.json", content)
    monkeypatch.setattr(cmu_evtol, "urlopen", lambda *args, **kwargs: _FakeResponse(content))
    manifest = download_cmu_evtol_files(
        mode="all",
        raw_dir=tmp_path / "raw",
        source_manifest_path=source_manifest,
        output_dir=tmp_path / "reports",
    )
    (tmp_path / "raw" / "fixture.csv").write_text("tampered\n", encoding="utf-8")

    rows = verify_raw_snapshot(manifest)

    assert rows[0]["hash_matches"] is False


def test_timeseries_parser_accepts_explicit_negative_discharge_energy_convention(tmp_path) -> None:
    csv_path = tmp_path / "fixture.csv"
    csv_path.write_text(_csv_text(), encoding="utf-8")

    summary = parse_timeseries_csv(csv_path)

    assert summary["quality_status"] == "passed"
    assert summary["pack_level_evidence"] is False
    assert summary["candidate_ranking_evidence"] is False
    assert (
        summary["source_sign_conventions"]["EnergyDischarge_W_h"]
        == "negative_discharge_energy_source_convention"
    )


@pytest.mark.parametrize(
    ("time_value", "voltage", "temperature"),
    [
        (-1.0, 3.7, 25.0),
        (0.0, 0.0, 25.0),
        (0.0, 3.7, 140.0),
    ],
)
def test_timeseries_parser_rejects_impossible_time_voltage_temperature(
    tmp_path,
    time_value,
    voltage,
    temperature,
) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text(_csv_text(time_value, voltage, temperature), encoding="utf-8")

    with pytest.raises(MeasurementQualityError):
        parse_timeseries_csv(csv_path)


def test_metadata_only_records_do_not_create_measurement_views(tmp_path) -> None:
    manifest = tmp_path / "raw_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "file_name": "fixture.csv",
                        "status": "metadata_only",
                        "parser_status": "not_attempted",
                        "local_path": str(tmp_path / "fixture.csv"),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    summary = build_measurement_summary(raw_manifest_path=manifest)

    assert summary["quality_status"] == "blocked"
    assert summary["audited_measurement_summary"] is False
    assert summary["timeseries_file_count"] == 0
