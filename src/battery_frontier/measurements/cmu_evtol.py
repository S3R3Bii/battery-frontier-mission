from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from battery_frontier import __version__
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.provenance import sha256_file

CMU_SOURCE_ID = "datasource.cmu_evtol_battery"
CMU_SOURCE_NAME = "Carnegie Mellon eVTOL Battery Dataset"
CMU_ARTICLE_URL = "https://kilthub.cmu.edu/articles/dataset/eVTOL_Battery_Dataset/14226830"
CMU_DOI = "10.1184/R1/14226830"
CMU_LICENSE = "CC BY 4.0"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "approved" / "cmu_evtol_battery"
DEFAULT_MEASUREMENT_DIR = PROJECT_ROOT / "reports" / "measurements"
RAW_MANIFEST_NAME = "cmu_evtol_raw_file_manifest.json"
MEASUREMENT_SUMMARY_NAME = "cmu_evtol_measurement_summary.json"
MEASUREMENT_REPORT_NAME = "cmu_evtol_measurement_summary.md"
FETCH_TIMEOUT_S = 120
USER_AGENT = "battery-frontier-mission/0.4 cmu-evtol-ingestion"

EXPECTED_TIMESERIES_COLUMNS = (
    "time_s",
    "Ecell_V",
    "I_mA",
    "EnergyCharge_W_h",
    "QCharge_mA_h",
    "EnergyDischarge_W_h",
    "QDischarge_mA_h",
    "Temperature__C",
    "cycleNumber",
    "Ns",
)

TIMESERIES_UNITS = {
    "time_s": "s",
    "Ecell_V": "V",
    "I_mA": "mA",
    "EnergyCharge_W_h": "Wh",
    "QCharge_mA_h": "mAh",
    "EnergyDischarge_W_h": "Wh",
    "QDischarge_mA_h": "mAh",
    "Temperature__C": "degC",
    "cycleNumber": "dimensionless",
    "Ns": "dimensionless",
}


class CmuEvtolIngestionError(RuntimeError):
    """Raised when CMU eVTOL raw snapshot or parser checks fail."""


class MeasurementQualityError(ValueError):
    """Raised when parsed measurement data violates physical/unit checks."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_cmu_source_manifest() -> Path | None:
    manifests = sorted(
        (PROJECT_ROOT / "reports" / "source-metadata").glob(
            "*-datasource_cmu_evtol_battery-manifest.json"
        )
    )
    return manifests[-1] if manifests else None


def load_cmu_source_records(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    path = manifest_path or latest_cmu_source_manifest()
    if path is None:
        raise CmuEvtolIngestionError(
            "No CMU source metadata manifest found. Run "
            "`python -m battery_frontier.cli source-dry-run --source "
            "datasource.cmu_evtol_battery --query 14226830 --rows 50 --execute "
            "--write-manifest --manifest-dir reports/source-metadata` first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("result", {}).get("records", payload.get("records", []))
    if not isinstance(records, list) or not records:
        raise CmuEvtolIngestionError(f"{_display_path(path)} does not contain CMU file records")
    return [record for record in records if isinstance(record, dict)]


def _sort_key_for_subset(record: dict[str, Any]) -> tuple[int, int, str]:
    name = str(record.get("file_name") or "")
    size = int(record.get("file_size_bytes") or 0)
    if name.lower() == "readme.txt":
        return (0, size, name)
    if name.lower().endswith("_impedance.csv"):
        return (2, size, name)
    if name.lower().endswith(".csv"):
        return (1, size, name)
    return (3, size, name)


def select_cmu_records(
    records: list[dict[str, Any]],
    *,
    mode: str = "subset",
    max_files: int | None = None,
) -> list[dict[str, Any]]:
    if mode not in {"metadata", "subset", "all"}:
        raise ValueError("mode must be one of: metadata, subset, all")
    ordered = sorted(records, key=_sort_key_for_subset)
    if mode in {"metadata", "all"}:
        selected = ordered
    else:
        readme = [record for record in ordered if str(record.get("file_name")) == "README.txt"]
        timeseries = [
            record
            for record in ordered
            if str(record.get("file_name", "")).lower().endswith(".csv")
            and "_impedance" not in str(record.get("file_name", "")).lower()
        ][:1]
        impedance = [
            record
            for record in ordered
            if str(record.get("file_name", "")).lower().endswith("_impedance.csv")
        ][:1]
        selected = [*readme[:1], *timeseries, *impedance]
    if max_files is not None:
        if max_files <= 0:
            raise ValueError("max_files must be positive")
        selected = selected[:max_files]
    return selected


def _disk_free_bytes(path: Path) -> int:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free


def _download_file(url: str, target: Path) -> None:
    request = Request(
        url,
        headers={"Accept": "*/*", "User-Agent": USER_AGENT},
        method="GET",
    )
    part = target.with_name(f"{target.name}.part")
    try:
        with urlopen(request, timeout=FETCH_TIMEOUT_S) as response:
            with part.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        part.replace(target)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        part.unlink(missing_ok=True)
        raise CmuEvtolIngestionError(f"failed downloading {url}: {exc}") from exc


def _raw_record(
    source_record: dict[str, Any],
    *,
    raw_dir: Path,
    status: str,
    parser_status: str,
    retrieval_timestamp_utc: str,
) -> dict[str, Any]:
    file_name = str(source_record.get("file_name") or "")
    local_path = raw_dir / file_name
    exists = local_path.exists()
    computed_sha256 = sha256_file(local_path) if exists else None
    computed_md5 = _file_md5(local_path) if exists else None
    local_size = local_path.stat().st_size if exists else None
    supplied_md5 = source_record.get("supplied_md5")
    return {
        "source_id": CMU_SOURCE_ID,
        "source": CMU_SOURCE_NAME,
        "article_url": CMU_ARTICLE_URL,
        "doi": CMU_DOI,
        "license": source_record.get("license") or CMU_LICENSE,
        "license_status": "approved",
        "file_id": source_record.get("file_id"),
        "file_name": file_name,
        "url": source_record.get("download_url"),
        "retrieval_timestamp_utc": retrieval_timestamp_utc,
        "published_date": source_record.get("published_date"),
        "modified_date": source_record.get("modified_date"),
        "supplied_md5": supplied_md5,
        "computed_md5": computed_md5,
        "computed_sha256": computed_sha256,
        "expected_size_bytes": source_record.get("file_size_bytes"),
        "local_size_bytes": local_size,
        "size_matches": (
            local_size == source_record.get("file_size_bytes") if local_size is not None else False
        ),
        "md5_matches": computed_md5 == supplied_md5 if computed_md5 and supplied_md5 else None,
        "local_path": _display_path(local_path),
        "status": status,
        "parser_status": parser_status,
        "system_boundary": "cell-level eVTOL duty-cycle experimental source",
        "evidence_label": "known_experimental",
        "performance_evidence": False,
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "raw_file_committed": False,
        "limitations": (
            "Raw file is approved source material, but measured values become usable only "
            "after hash verification, parser validation, unit checks, and explicit "
            "cell-level boundary tagging."
        ),
    }


def download_cmu_evtol_files(
    *,
    mode: str = "metadata",
    raw_dir: Path | None = None,
    max_files: int | None = None,
    force: bool = False,
    source_manifest_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    records = load_cmu_source_records(source_manifest_path)
    selected = select_cmu_records(records, mode=mode, max_files=max_files)
    destination = raw_dir or DEFAULT_RAW_DIR
    report_dir = output_dir or DEFAULT_MEASUREMENT_DIR
    destination.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    selected_size = sum(int(record.get("file_size_bytes") or 0) for record in selected)
    free_bytes = _disk_free_bytes(destination)
    if mode != "metadata" and selected_size > free_bytes * 0.9:
        raise CmuEvtolIngestionError(
            f"Not enough free disk for CMU download. Selected bytes={selected_size}; "
            f"free bytes={free_bytes}. Use `--mode subset` or free disk space."
        )

    retrieval_timestamp = _utc_now()
    manifest_records: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    total_downloaded = 0
    for record in selected:
        file_name = str(record.get("file_name") or "")
        target = destination / file_name
        if mode == "metadata":
            status = "metadata_only"
            parser_status = "not_attempted"
        elif target.exists() and not force:
            status = "already_present"
            parser_status = "not_attempted"
        else:
            download_url = record.get("download_url")
            if not isinstance(download_url, str) or not download_url:
                raise CmuEvtolIngestionError(f"missing download URL for {file_name}")
            _download_file(download_url, target)
            status = "downloaded"
            parser_status = "not_attempted"
            total_downloaded += target.stat().st_size
        manifest_record = _raw_record(
            record,
            raw_dir=destination,
            status=status,
            parser_status=parser_status,
            retrieval_timestamp_utc=retrieval_timestamp,
        )
        md5_mismatch = (
            target.exists()
            and manifest_record["supplied_md5"]
            and not manifest_record["md5_matches"]
        )
        if md5_mismatch:
            raise CmuEvtolIngestionError(
                f"MD5 mismatch for {file_name}: expected {manifest_record['supplied_md5']} "
                f"got {manifest_record['computed_md5']}"
            )
        manifest_records.append(manifest_record)
        status_counts[status] += 1

    payload = {
        "artifact_type": "experimental_source_snapshot",
        "source_id": CMU_SOURCE_ID,
        "source": CMU_SOURCE_NAME,
        "article_url": CMU_ARTICLE_URL,
        "doi": CMU_DOI,
        "license": CMU_LICENSE,
        "license_status": "approved",
        "generated_at_utc": _utc_now(),
        "retrieval_timestamp_utc": retrieval_timestamp,
        "mode": mode,
        "selected_file_count": len(selected),
        "metadata_file_count": len(records),
        "selected_size_bytes": selected_size,
        "downloaded_size_bytes": total_downloaded,
        "raw_dir": _display_path(destination),
        "raw_files_committed": False,
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_label": "known_experimental",
        "system_boundary": "cell-level eVTOL duty-cycle evidence only",
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "performance_evidence": False,
        "records": manifest_records,
        "limitations": [
            "Metadata and raw files are not pack-level proof.",
            "Raw files are not candidate-ranking evidence.",
            "Measured values are usable only after parser and unit checks pass.",
            "Do not commit raw large files unless Git LFS is explicitly configured.",
        ],
    }
    target_manifest = report_dir / RAW_MANIFEST_NAME
    target_manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return target_manifest


def verify_raw_snapshot(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    path = manifest_path or DEFAULT_MEASUREMENT_DIR / RAW_MANIFEST_NAME
    if not path.exists():
        raise CmuEvtolIngestionError(
            f"Raw manifest not found: {_display_path(path)}. Run source-fetch-cmu-evtol first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for record in payload.get("records", []):
        local_path = PROJECT_ROOT / record["local_path"]
        exists = local_path.exists()
        current_sha256 = sha256_file(local_path) if exists else None
        current_md5 = _file_md5(local_path) if exists else None
        expected_size = record.get("expected_size_bytes")
        expected_sha256 = record.get("computed_sha256")
        supplied_md5 = record.get("supplied_md5")
        local_size = local_path.stat().st_size if exists else None
        rows.append(
            {
                "file_name": record["file_name"],
                "exists": exists,
                "status": record["status"],
                "parser_status": record["parser_status"],
                "expected_size_bytes": expected_size,
                "local_size_bytes": local_size,
                "size_matches": (
                    bool(exists and local_size == expected_size)
                    if expected_size is not None
                    else None
                ),
                "expected_sha256": expected_sha256,
                "current_sha256": current_sha256,
                "hash_matches": bool(
                    exists
                    and expected_sha256
                    and current_sha256 == expected_sha256
                ),
                "supplied_md5": supplied_md5,
                "current_md5": current_md5,
                "md5_matches": bool(
                    exists and supplied_md5 and current_md5 == supplied_md5
                ),
            }
        )
    return rows


def _read_csv(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    if max_rows is not None and max_rows <= 0:
        raise ValueError("max_rows must be positive")
    return pd.read_csv(path, nrows=max_rows)


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise MeasurementQualityError(f"missing required column: {column}")
    series = pd.to_numeric(frame[column], errors="coerce")
    if series.isna().all():
        raise MeasurementQualityError(f"column has no numeric values: {column}")
    return series


def parse_timeseries_csv(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    frame = _read_csv(path, max_rows=max_rows)
    missing_columns = [column for column in EXPECTED_TIMESERIES_COLUMNS if column not in frame]
    if missing_columns:
        raise MeasurementQualityError(
            f"{path.name} missing expected columns: {', '.join(missing_columns)}"
        )

    time_s = _numeric_series(frame, "time_s")
    voltage_v = _numeric_series(frame, "Ecell_V")
    current_m_a = _numeric_series(frame, "I_mA")
    temperature_c = _numeric_series(frame, "Temperature__C")
    cycle_number = _numeric_series(frame, "cycleNumber")

    failures: list[str] = []
    if (time_s < 0).any():
        failures.append("negative absolute time")
    if (voltage_v <= 0).any() or (voltage_v > 5.5).any():
        failures.append("voltage outside positive plausible lithium-ion cell range")
    if (temperature_c < -50).any() or (temperature_c > 120).any():
        failures.append("temperature outside explicit Celsius plausibility range")
    if (cycle_number < 0).any():
        failures.append("negative cycle number")
    for column in ("EnergyCharge_W_h", "QCharge_mA_h", "QDischarge_mA_h"):
        series = _numeric_series(frame, column)
        if (series.dropna() < 0).any():
            failures.append(f"negative {column}")
    discharge_energy = _numeric_series(frame, "EnergyDischarge_W_h")
    discharge_nonzero = discharge_energy[discharge_energy != 0].dropna()
    discharge_energy_sign = "zero_or_empty"
    if not discharge_nonzero.empty:
        if (discharge_nonzero < 0).all():
            discharge_energy_sign = "negative_discharge_energy_source_convention"
        elif (discharge_nonzero > 0).all():
            discharge_energy_sign = "positive_discharge_energy_source_convention"
        else:
            failures.append("mixed sign EnergyDischarge_W_h")
    if failures:
        raise MeasurementQualityError(f"{path.name} quality check failed: {'; '.join(failures)}")

    duplicate_timestamps = int(time_s.duplicated().sum())
    current_counts = {
        "positive": int((current_m_a > 0).sum()),
        "negative": int((current_m_a < 0).sum()),
        "zero": int((current_m_a == 0).sum()),
    }
    capacity_checks = {}
    for column in ("QCharge_mA_h", "QDischarge_mA_h"):
        capacity = _numeric_series(frame, column)
        negative_steps = 0
        for _, group in frame.assign(_capacity=capacity).groupby("cycleNumber", dropna=False):
            negative_steps += int((group["_capacity"].diff().dropna() < -1e-6).sum())
        capacity_checks[column] = {
            "monotonicity_scope": "within reported cycleNumber groups",
            "negative_step_count": negative_steps,
            "cycle_number_caveat": (
                "CMU README states cycleNumber is not accurate; treat cycle grouping as "
                "a quality hint, not a validated lifecycle index."
            ),
        }

    return {
        "artifact_type": "parsed_cell_timeseries",
        "source_id": CMU_SOURCE_ID,
        "file_name": path.name,
        "local_path": _display_path(path),
        "parsed_at_utc": _utc_now(),
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "units": TIMESERIES_UNITS,
        "system_boundary": "cell-level eVTOL duty-cycle",
        "evidence_label": "known_experimental",
        "performance_evidence": True,
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "quality_status": "passed",
        "missing_values_by_column": {
            column: int(frame[column].isna().sum()) for column in EXPECTED_TIMESERIES_COLUMNS
        },
        "duplicate_timestamp_count": duplicate_timestamps,
        "time_s": {
            "min": float(time_s.min()),
            "max": float(time_s.max()),
            "negative_count": int((time_s < 0).sum()),
        },
        "voltage_V": {
            "min": float(voltage_v.min()),
            "max": float(voltage_v.max()),
            "mean": float(voltage_v.mean()),
        },
        "current_mA": {
            "min": float(current_m_a.min()),
            "max": float(current_m_a.max()),
            "mean": float(current_m_a.mean()),
            "sign_convention": (
                "positive, negative, and zero counts are reported from the source column; "
                "charge/discharge interpretation still requires protocol audit."
            ),
            "sign_counts": current_counts,
        },
        "temperature_C": {
            "min": float(temperature_c.min()),
            "max": float(temperature_c.max()),
            "mean": float(temperature_c.mean()),
        },
        "capacity_monotonicity": capacity_checks,
        "source_sign_conventions": {
            "current_mA": (
                "source column preserves signed current; charge/discharge mapping "
                "requires protocol-level audit"
            ),
            "EnergyDischarge_W_h": discharge_energy_sign,
            "QDischarge_mA_h": "nonnegative cumulative discharge capacity in selected rows",
        },
        "limitations": [
            "Cell-level evidence only.",
            "No pack overhead, aircraft integration, reserve, safety, or certification proof.",
            "Not candidate-ranking evidence.",
        ],
    }


def parse_impedance_csv(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    frame = _read_csv(path, max_rows=max_rows)
    numeric_columns = [
        column
        for column in frame.columns
        if pd.to_numeric(frame[column], errors="coerce").notna().any()
    ]
    if not numeric_columns:
        raise MeasurementQualityError(f"{path.name} has no numeric impedance columns")
    return {
        "artifact_type": "impedance_summary",
        "source_id": CMU_SOURCE_ID,
        "file_name": path.name,
        "local_path": _display_path(path),
        "parsed_at_utc": _utc_now(),
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "numeric_columns": numeric_columns,
        "missing_values_by_column": {
            column: int(frame[column].isna().sum()) for column in frame.columns
        },
        "system_boundary": "cell-level impedance evidence",
        "evidence_label": "known_experimental",
        "performance_evidence": True,
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "quality_status": "passed",
        "limitations": [
            "Impedance evidence is cell-level and file-schema-specific.",
            "No pack-level or candidate-ranking claim is created.",
        ],
    }


def _raw_records_for_parsing(raw_manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    return [
        record
        for record in payload.get("records", [])
        if record.get("status") != "metadata_only" and Path(record["local_path"]).suffix == ".csv"
    ]


def build_measurement_summary(
    *,
    raw_manifest_path: Path | None = None,
    max_files: int | None = 3,
    max_rows_per_file: int | None = 50_000,
) -> dict[str, Any]:
    path = raw_manifest_path or DEFAULT_MEASUREMENT_DIR / RAW_MANIFEST_NAME
    if not path.exists():
        raise CmuEvtolIngestionError(
            f"Raw manifest not found: {_display_path(path)}. Run source-fetch-cmu-evtol first."
        )
    verification_rows = verify_raw_snapshot(path)
    failed_verification = [
        row
        for row in verification_rows
        if row["status"] != "metadata_only" and not row["hash_matches"]
    ]
    if failed_verification:
        failed = ", ".join(row["file_name"] for row in failed_verification)
        raise CmuEvtolIngestionError(f"raw snapshot hash verification failed for: {failed}")

    records = _raw_records_for_parsing(path)
    if max_files is not None:
        if max_files <= 0:
            raise ValueError("max_files must be positive")
        records = records[:max_files]

    parsed_timeseries: list[dict[str, Any]] = []
    parsed_impedance: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for record in records:
        local_path = PROJECT_ROOT / record["local_path"]
        try:
            if local_path.name.lower().endswith("_impedance.csv"):
                parsed_impedance.append(parse_impedance_csv(local_path, max_rows_per_file))
            else:
                parsed_timeseries.append(parse_timeseries_csv(local_path, max_rows_per_file))
        except MeasurementQualityError as exc:
            failures.append({"file_name": local_path.name, "error": str(exc)})

    status = "passed" if records and not failures else "blocked"
    return {
        "artifact_type": "measurement_quality_report",
        "source_id": CMU_SOURCE_ID,
        "source": CMU_SOURCE_NAME,
        "article_url": CMU_ARTICLE_URL,
        "doi": CMU_DOI,
        "license": CMU_LICENSE,
        "license_status": "approved",
        "generated_at_utc": _utc_now(),
        "package_version": __version__,
        "raw_manifest_path": _display_path(path),
        "quality_status": status,
        "evidence_label": "known_experimental",
        "system_boundary": "cell-level eVTOL duty-cycle evidence only",
        "pack_level_evidence": False,
        "candidate_ranking_evidence": False,
        "audited_measurement_summary": status == "passed",
        "timeseries_file_count": len(parsed_timeseries),
        "impedance_file_count": len(parsed_impedance),
        "failed_file_count": len(failures),
        "parsed_cell_timeseries": parsed_timeseries,
        "cell_cycle_summary": [
            {
                "file_name": row["file_name"],
                "row_count": row["row_count"],
                "time_s_max": row["time_s"]["max"],
                "voltage_min_V": row["voltage_V"]["min"],
                "voltage_max_V": row["voltage_V"]["max"],
                "temperature_min_C": row["temperature_C"]["min"],
                "temperature_max_C": row["temperature_C"]["max"],
                "current_sign_counts": row["current_mA"]["sign_counts"],
                "system_boundary": row["system_boundary"],
                "pack_level_evidence": False,
                "candidate_ranking_evidence": False,
            }
            for row in parsed_timeseries
        ],
        "impedance_summary": parsed_impedance,
        "verification": verification_rows,
        "failures": failures,
        "limitations": [
            "This is cell-level experimental evidence from one approved dataset.",
            "The report does not create pack-level proof.",
            "The report does not allow candidate or chemistry ranking.",
            "Protocol details and cycleNumber caveats still require deeper audit.",
        ],
    }


def _write_measurement_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CMU eVTOL Measurement Summary",
        "",
        "> Approved CC BY 4.0 cell-level evidence. Not pack-level proof and not",
        "> candidate-ranking evidence.",
        "",
        "## Status",
        "",
        f"- Quality status: {payload['quality_status']}",
        f"- Timeseries files parsed: {payload['timeseries_file_count']}",
        f"- Impedance files parsed: {payload['impedance_file_count']}",
        f"- Failed files: {payload['failed_file_count']}",
        f"- System boundary: {payload['system_boundary']}",
        f"- Pack-level evidence: {payload['pack_level_evidence']}",
        f"- Candidate-ranking evidence: {payload['candidate_ranking_evidence']}",
        "",
        "## Parsed Timeseries",
        "",
    ]
    if payload["cell_cycle_summary"]:
        lines.append("| File | Rows | Voltage V | Temperature C | Current sign counts |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for row in payload["cell_cycle_summary"]:
            signs = json.dumps(row["current_sign_counts"], sort_keys=True)
            lines.append(
                f"| `{row['file_name']}` | {row['row_count']} | "
                f"{row['voltage_min_V']:.3f}-{row['voltage_max_V']:.3f} | "
                f"{row['temperature_min_C']:.2f}-{row['temperature_max_C']:.2f} | "
                f"`{signs}` |"
            )
    else:
        lines.append("No timeseries file has passed parsing yet.")
    lines.extend(
        [
            "",
            "## Failures",
            "",
        ]
    )
    if payload["failures"]:
        lines.extend(f"- `{row['file_name']}`: {row['error']}" for row in payload["failures"])
    else:
        lines.append("No parser failures in the selected batch.")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in payload["limitations"]],
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_measurement_summary(
    *,
    raw_manifest_path: Path | None = None,
    output_dir: Path | None = None,
    max_files: int | None = 3,
    max_rows_per_file: int | None = 50_000,
) -> tuple[Path, Path]:
    destination = output_dir or DEFAULT_MEASUREMENT_DIR
    destination.mkdir(parents=True, exist_ok=True)
    payload = build_measurement_summary(
        raw_manifest_path=raw_manifest_path,
        max_files=max_files,
        max_rows_per_file=max_rows_per_file,
    )
    json_path = destination / MEASUREMENT_SUMMARY_NAME
    markdown_path = destination / MEASUREMENT_REPORT_NAME
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    _write_measurement_markdown(payload, markdown_path)
    return json_path, markdown_path
