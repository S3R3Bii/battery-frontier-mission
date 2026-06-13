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
            headers={"Accept": "application/json", **request_spec.headers},
            method=request_spec.method,
        )
        with urlopen(request, timeout=FETCH_TIMEOUT_S) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return request_spec, payload, self.parse_records(payload)


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


class MaterialsProjectConnector(SourceConnector):
    source_id = "datasource.materials_project"
    connector_name = "Materials Project mp-api client"
    requires_key = True
    key_env = "MP_API_KEY"
    execution_supported = False

    def build_request(self, query: str, rows: int) -> SourceRequest:
        return SourceRequest(
            method="CLIENT",
            url="mp-api MPRester.materials.summary.search",
            headers={"Authorization": "MP_API_KEY environment variable required"},
            query=query,
            rows=rows,
        )


CONNECTORS: dict[str, SourceConnector] = {
    connector.source_id: connector
    for connector in (
        MaterialsProjectConnector(),
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
