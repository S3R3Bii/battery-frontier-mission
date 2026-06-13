from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from battery_frontier.config import PROJECT_ROOT
from battery_frontier.registry import Registries
from battery_frontier.schemas import DataSource

DEFAULT_SOURCE_QUERY = "battery aviation energy storage"
DEFAULT_SOURCE_ROWS = 5
FETCH_TIMEOUT_S = 30
SOURCE_USER_AGENT = "battery-frontier-mission/0.4 metadata-only"
MATERIALS_PROJECT_FIELDS = (
    "material_id",
    "formula_pretty",
    "chemsys",
    "elements",
    "density",
    "energy_above_hull",
    "formation_energy_per_atom",
    "is_stable",
    "theoretical",
    "last_updated",
)
MATERIALS_PROJECT_DEFAULT_ELEMENTS = ("Li", "O")
_ELEMENT_SYMBOLS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
}


@dataclass(frozen=True)
class SourceRequest:
    method: str
    url: str
    headers: dict[str, str]
    query: str
    rows: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "query": self.query,
            "rows": self.rows,
        }


class SourceConnector:
    source_id = ""
    connector_name = "generic metadata connector"
    requires_key = False
    key_env: str | None = None
    execution_supported = False
    metadata_only = True

    def credential_available(self) -> bool:
        return self.key_env is None or bool(os.environ.get(self.key_env))

    def readiness_note(self) -> str:
        if self.requires_key and not self.credential_available():
            return f"requires `{self.key_env}` before API execution"
        if not self.execution_supported:
            return "request metadata only; execution is intentionally disabled"
        return "ready for optional metadata fetch"

    def build_request(self, query: str, rows: int) -> SourceRequest:
        url = "manual_review_required"
        return SourceRequest(
            method="GET",
            url=url,
            headers={"Accept": "application/json"},
            query=query,
            rows=rows,
        )

    def parse_records(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [record for record in payload if isinstance(record, dict)]
        if isinstance(payload, dict):
            for key in ("results", "records", "data", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [record for record in value if isinstance(record, dict)]
            return [payload]
        return []

    def fetch(self, query: str, rows: int) -> tuple[SourceRequest, Any, list[dict[str, Any]]]:
        if self.requires_key and not self.credential_available():
            raise RuntimeError(f"{self.source_id} requires `{self.key_env}`")
        if not self.execution_supported:
            raise RuntimeError(f"{self.source_id} does not support direct execution")

        request_spec = self.build_request(query, rows)
        request = Request(
            request_spec.url,
            headers={
                "Accept": "application/json",
                "User-Agent": SOURCE_USER_AGENT,
                **request_spec.headers,
            },
            method=request_spec.method,
        )
        with urlopen(request, timeout=FETCH_TIMEOUT_S) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return request_spec, payload, self.parse_records(payload)


def _extract_element_symbols(query: str) -> list[str]:
    separators = ",;:/|+()[]{}"
    normalized = query
    for separator in separators:
        normalized = normalized.replace(separator, " ")
    normalized = normalized.replace("-", " ")

    symbols: list[str] = []
    for raw_token in normalized.split():
        token = raw_token.strip()
        if not token:
            continue
        candidate = token[0].upper() + token[1:].lower()
        if candidate in _ELEMENT_SYMBOLS and candidate not in symbols:
            symbols.append(candidate)
    return symbols


class NasaNtrsConnector(SourceConnector):
    source_id = "datasource.nasa_ntrs"
    connector_name = "NASA NTRS metadata search"
    execution_supported = True

    def build_request(self, query: str, rows: int) -> SourceRequest:
        params = urlencode({"keyword": query, "size": rows})
        return SourceRequest(
            method="GET",
            url=f"https://ntrs.nasa.gov/api/citations/search?{params}",
            headers={"Accept": "application/json"},
            query=query,
            rows=rows,
        )


class OstiConnector(SourceConnector):
    source_id = "datasource.osti"
    connector_name = "DOE OSTI metadata search"
    execution_supported = True

    def build_request(self, query: str, rows: int) -> SourceRequest:
        params = urlencode({"q": query, "rows": rows})
        return SourceRequest(
            method="GET",
            url=f"https://www.osti.gov/api/v1/records?{params}",
            headers={"Accept": "application/json"},
            query=query,
            rows=rows,
        )


class PubChemConnector(SourceConnector):
    source_id = "datasource.pubchem"
    connector_name = "PubChem PUG REST property lookup"
    execution_supported = False

    def build_request(self, query: str, rows: int) -> SourceRequest:
        compound = quote(query.strip() or "lithium")
        return SourceRequest(
            method="GET",
            url=(
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                f"{compound}/property/MolecularFormula,MolecularWeight/JSON"
            ),
            headers={"Accept": "application/json"},
            query=query,
            rows=rows,
        )


class FigshareArticleConnector(SourceConnector):
    source_id = "datasource.cmu_evtol_battery"
    connector_name = "Figshare/KiltHub approved article metadata"
    execution_supported = True

    def build_request(self, query: str, rows: int) -> SourceRequest:
        article_id = query.strip() or "14226830"
        if not article_id.isdigit():
            article_id = "14226830"
        return SourceRequest(
            method="GET",
            url=f"https://api.figshare.com/v2/articles/{article_id}",
            headers={"Accept": "application/json"},
            query=article_id,
            rows=rows,
        )

    def parse_records(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []

        files = payload.get("files")
        if not isinstance(files, list):
            files = []

        article_license = payload.get("license")
        license_name = None
        license_url = None
        if isinstance(article_license, dict):
            license_name = article_license.get("name")
            license_url = article_license.get("url")

        article = {
            "article_id": payload.get("id"),
            "article_title": payload.get("title"),
            "article_doi": payload.get("doi"),
            "article_url": payload.get("url_public_html") or payload.get("url"),
            "article_version": payload.get("version"),
            "published_date": payload.get("published_date"),
            "modified_date": payload.get("modified_date"),
            "license": license_name,
            "license_url": license_url,
        }

        records: list[dict[str, Any]] = []
        for file_record in files:
            if not isinstance(file_record, dict):
                continue
            record = {
                **article,
                "record_type": "approved_experimental_dataset_file_metadata",
                "metadata_only": True,
                "ranking_evidence": False,
                "performance_evidence": False,
                "system_boundary": (
                    "cell-level experimental eVTOL duty-cycle data; file metadata only"
                ),
                "evidence_class": "known_experimental",
                "measurement_status": "measurement_file_not_ingested_or_audited",
                "file_id": file_record.get("id"),
                "file_name": file_record.get("name"),
                "file_size_bytes": file_record.get("size"),
                "download_url": file_record.get("download_url"),
                "supplied_md5": file_record.get("supplied_md5"),
                "limitations": (
                    "Approved CC BY 4.0 source metadata. The file itself must be "
                    "downloaded, hashed, parsed, unit-audited, and mapped to cell-level "
                    "system boundaries before any measured values can be used. This is "
                    "not pack-level proof or ranking evidence."
                ),
            }
            records.append(record)

        if records:
            return records

        return [
            {
                **article,
                "record_type": "approved_experimental_dataset_article_metadata",
                "metadata_only": True,
                "ranking_evidence": False,
                "performance_evidence": False,
                "system_boundary": (
                    "cell-level experimental eVTOL duty-cycle data; article metadata only"
                ),
                "evidence_class": "known_experimental",
                "measurement_status": "measurement_files_not_listed_or_audited",
                "limitations": (
                    "Approved source metadata only; no measured values have been parsed."
                ),
            }
        ]


class MaterialsProjectConnector(SourceConnector):
    source_id = "datasource.materials_project"
    connector_name = "Materials Project summary metadata API"
    requires_key = True
    key_env = "MP_API_KEY"
    execution_supported = True

    def build_request(self, query: str, rows: int) -> SourceRequest:
        elements = _extract_element_symbols(query) or list(MATERIALS_PROJECT_DEFAULT_ELEMENTS)
        params = urlencode(
            {
                "elements": ",".join(elements),
                "_fields": ",".join(MATERIALS_PROJECT_FIELDS),
                "_limit": rows,
            }
        )
        return SourceRequest(
            method="GET",
            url=f"https://api.materialsproject.org/materials/summary/?{params}",
            headers={
                "Accept": "application/json",
                "X-API-KEY": f"<env:{self.key_env}>",
            },
            query=query,
            rows=rows,
        )

    def parse_records(self, payload: Any) -> list[dict[str, Any]]:
        records = super().parse_records(payload)
        normalized: list[dict[str, Any]] = []
        for record in records:
            item = {field: record.get(field) for field in MATERIALS_PROJECT_FIELDS}
            item.update(
                {
                    "record_type": "computed_material_metadata",
                    "metadata_only": True,
                    "ranking_evidence": False,
                    "performance_evidence": False,
                    "system_boundary": "computed material metadata, not cell or pack performance",
                    "evidence_class": "simulation_estimate",
                    "limitations": (
                        "Materials Project values are computed/material metadata. They do not "
                        "validate battery performance, cycle life, manufacturability, safety, "
                        "or aviation usefulness."
                    ),
                }
            )
            normalized.append(item)
        return normalized

    def fetch(self, query: str, rows: int) -> tuple[SourceRequest, Any, list[dict[str, Any]]]:
        if self.requires_key and not self.credential_available():
            raise RuntimeError(f"{self.source_id} requires `{self.key_env}`")

        request_spec = self.build_request(query, rows)
        request = Request(
            request_spec.url,
            headers={
                "Accept": "application/json",
                "User-Agent": SOURCE_USER_AGENT,
                "X-API-KEY": os.environ[str(self.key_env)],
            },
            method=request_spec.method,
        )
        with urlopen(request, timeout=FETCH_TIMEOUT_S) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return request_spec, payload, self.parse_records(payload)


CONNECTORS: dict[str, SourceConnector] = {
    connector.source_id: connector
    for connector in (
        MaterialsProjectConnector(),
        FigshareArticleConnector(),
        NasaNtrsConnector(),
        OstiConnector(),
        PubChemConnector(),
    )
}


def connector_for_source(source_id: str) -> SourceConnector:
    return CONNECTORS.get(source_id, SourceConnector())


def source_status_rows(registries: Registries) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in registries.data_sources:
        connector = connector_for_source(source.id)
        rows.append(
            {
                "source_id": source.id,
                "source": source.name,
                "license_status": source.license_status,
                "ingestion_status": source.ingestion_status,
                "connector": connector.connector_name,
                "requires_key": connector.requires_key,
                "key_env": connector.key_env,
                "credential_available": connector.credential_available(),
                "execution_supported": connector.execution_supported,
                "metadata_only": connector.metadata_only,
                "trusted_publication_allowed": source.license_status == "approved",
                "readiness": connector.readiness_note(),
                "limitations": source.limitations,
            }
        )
    return rows


def _find_source(registries: Registries, source_id: str) -> DataSource:
    for source in registries.data_sources:
        if source.id == source_id:
            return source
    raise ValueError(f"unknown source id: {source_id}")


def _failure_message(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}: {exc.reason}"
    if isinstance(exc, URLError):
        return f"URL error: {exc.reason}"
    return str(exc)


def dry_run_source(
    registries: Registries,
    source_id: str,
    *,
    query: str = DEFAULT_SOURCE_QUERY,
    rows: int = DEFAULT_SOURCE_ROWS,
    execute: bool = False,
) -> dict[str, Any]:
    if rows <= 0:
        raise ValueError("rows must be positive")

    source = _find_source(registries, source_id)
    connector = connector_for_source(source.id)
    request = connector.build_request(query, rows)
    generated_at = datetime.now(UTC).isoformat()
    trusted_publication = source.license_status == "approved"
    result: dict[str, Any] = {
        "source_id": source.id,
        "source": source.name,
        "generated_at_utc": generated_at,
        "query": query,
        "requested_rows": rows,
        "license_status": source.license_status,
        "license_note": source.license_note,
        "ingestion_status": source.ingestion_status,
        "limitations": source.limitations,
        "connector": connector.connector_name,
        "requires_key": connector.requires_key,
        "key_env": connector.key_env,
        "credential_available": connector.credential_available(),
        "execution_supported": connector.execution_supported,
        "execute_requested": execute,
        "executed": False,
        "request": request.as_dict(),
        "record_count": 0,
        "records": [],
        "metadata_only": connector.metadata_only,
        "trusted_publication": False,
        "ranking_evidence": False,
        "status": "dry_run",
        "notes": [
            "Metadata-only connector output is not battery performance evidence.",
            "Chemistry ranking remains blocked until audited measurements exist.",
        ],
    }
    if not trusted_publication:
        result["notes"].append(
            "Source license is not approved for trusted published snapshots."
        )
    if connector.requires_key and not connector.credential_available():
        result["status"] = "blocked_requires_key"
        return result
    if execute and not connector.execution_supported:
        result["status"] = "blocked_execution_not_supported"
        return result
    if not execute:
        return result

    try:
        executed_request, payload, records = connector.fetch(query, rows)
    except Exception as exc:
        result["status"] = "api_error"
        result["error_message"] = _failure_message(exc)
        return result

    result.update(
        {
            "executed": True,
            "status": "fetched",
            "request": executed_request.as_dict(),
            "record_count": len(records),
            "records": records,
            "response_sha256": hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            "trusted_publication": trusted_publication,
        }
    )
    return result


def write_snapshot_manifest(
    result: dict[str, Any],
    *,
    output_dir: Path | None = None,
) -> Path:
    destination = output_dir or PROJECT_ROOT / "data" / "raw" / "manifests"
    destination.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, sort_keys=True, default=str).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    source_id = str(result["source_id"]).replace(".", "_")
    target = destination / f"{timestamp}-{source_id}-manifest.json"
    manifest = {
        "artifact_type": "source_snapshot_manifest",
        "source_id": result["source_id"],
        "source": result["source"],
        "created_at_utc": datetime.now(UTC).isoformat(),
        "retrieved_at_utc": result["generated_at_utc"],
        "query": result["query"],
        "requested_rows": result["requested_rows"],
        "row_count": result["record_count"],
        "license_status": result["license_status"],
        "ingestion_status": result["ingestion_status"],
        "metadata_only": result["metadata_only"],
        "trusted_publication": bool(result["trusted_publication"]),
        "ranking_evidence": bool(result["ranking_evidence"]),
        "status": result["status"],
        "limitations": result["limitations"],
        "request": result["request"],
        "payload_sha256": digest,
        "result": result,
    }
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return target
