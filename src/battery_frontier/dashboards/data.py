from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from battery_frontier.config import PROJECT_ROOT
from battery_frontier.provenance import sha256_file
from battery_frontier.registry import Registries
from battery_frontier.reporting.method_cards import generate_dashboard_artifacts


@dataclass(frozen=True)
class DashboardBundle:
    manifest: dict[str, Any]
    physics: dict[str, Any]
    aviation: dict[str, Any]
    manifest_path: Path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dashboard_bundle() -> DashboardBundle:
    manifest_path, _ = generate_dashboard_artifacts()
    manifest = _read_json(manifest_path)
    artifact_paths = {
        artifact["artifact_id"]: PROJECT_ROOT / artifact["path"]
        for artifact in manifest["artifacts"]
    }
    return DashboardBundle(
        manifest=manifest,
        physics=_read_json(artifact_paths["artifact.phase2.results"]),
        aviation=_read_json(artifact_paths["artifact.phase3.results"]),
        manifest_path=manifest_path,
    )


def verify_dashboard_artifacts(bundle: DashboardBundle) -> pd.DataFrame:
    rows = []
    for artifact in bundle.manifest["artifacts"]:
        path = PROJECT_ROOT / artifact["path"]
        exists = path.exists()
        current_hash = sha256_file(path) if exists else None
        rows.append(
            {
                "artifact": artifact["title"],
                "type": artifact["artifact_type"],
                "exists": exists,
                "hash_matches": exists and current_hash == artifact["sha256"],
                "evidence status": artifact["evidence_status"],
                "claim boundary": artifact["public_claim_boundary"],
                "path": artifact["path"],
                "sha256": artifact["sha256"],
            }
        )
    return pd.DataFrame(rows)


def phase_readiness_frame(registries: Registries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "phase": "0",
                "component": "Scientific scope and boundaries",
                "status": "complete",
                "evidence gate": "documented and executable",
            },
            {
                "phase": "1",
                "component": "Schema and literature registry",
                "status": "foundation complete",
                "evidence gate": "first licensed snapshot pending",
            },
            {
                "phase": "2",
                "component": "Baseline physics",
                "status": "local foundation complete",
                "evidence gate": "audited literature validation pending",
            },
            {
                "phase": "3",
                "component": "Aviation mission simulator",
                "status": "local foundation complete",
                "evidence gate": "published-aircraft validation pending",
            },
            {
                "phase": "4",
                "component": "Scientific dashboard",
                "status": "prototype active",
                "evidence gate": "audited chemistry measurements pending",
            },
            {
                "phase": "5",
                "component": "ML screening",
                "status": "not started",
                "evidence gate": "validated training dataset required",
            },
        ]
    )


def evidence_ledger_frame(bundle: DashboardBundle) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for case in bundle.physics["cases"]:
        rows.append(
            {
                "record": case["name"],
                "domain": "physics",
                "evidence class": case["evidence_class"],
                "boundary": case["mass_basis_description"],
                "status": case["status"],
                "limitations": case["uncertainty_note"].strip(),
            }
        )
    for case in bundle.aviation["cases"]:
        rows.append(
            {
                "record": case["name"],
                "domain": "aviation",
                "evidence class": case["evidence_class"],
                "boundary": "segmented aircraft mission",
                "status": "feasible fixture" if case["feasible"] else "infeasible fixture",
                "limitations": case["uncertainty_note"].strip(),
            }
        )
    return pd.DataFrame(rows)


def physics_boundary_frame(bundle: DashboardBundle) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for case in bundle.physics["cases"]:
        if "active_specific_energy_Wh_kg" not in case:
            continue
        rows.append(
            {
                "case": case["name"],
                "boundary": "active reactants",
                "specific energy (Wh/kg)": case["active_specific_energy_Wh_kg"],
                "volumetric energy (Wh/L)": case.get(
                    "packed_active_volumetric_energy_Wh_l"
                ),
                "evidence": case["active_specific_energy_evidence_class"],
            }
        )
        if "cell" in case:
            rows.append(
                {
                    "case": case["name"],
                    "boundary": "complete cell",
                    "specific energy (Wh/kg)": case["cell"]["specific_energy_Wh_kg"],
                    "volumetric energy (Wh/L)": case["cell"]["volumetric_energy_Wh_l"],
                    "evidence": case["cell"]["evidence_class"],
                }
            )
        if "pack" in case:
            rows.append(
                {
                    "case": case["name"],
                    "boundary": "complete pack",
                    "specific energy (Wh/kg)": case["pack"]["specific_energy_Wh_kg"],
                    "volumetric energy (Wh/L)": case["pack"]["volumetric_energy_Wh_l"],
                    "evidence": case["pack"]["evidence_class"],
                }
            )
    return pd.DataFrame(rows)


def chemistry_readiness_frame(registries: Registries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "chemistry family": chemistry.name,
                "evidence context": chemistry.evidence_class.value,
                "ranking status": chemistry.status,
                "required metric count": len(chemistry.required_metrics),
                "constraint count": len(chemistry.known_constraints),
                "citations registered": len(chemistry.citation_ids),
            }
            for chemistry in registries.chemistries
        ]
    )


def source_readiness_frame(registries: Registries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source": source.name,
                "license status": source.license_status,
                "ingestion status": source.ingestion_status,
                "reliability rating": source.reliability_rating,
                "variables": ", ".join(source.variables),
                "limitations": source.limitations,
                "url": str(source.url),
            }
            for source in registries.data_sources
        ]
    )


def citation_readiness_frame(registries: Registries) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "citation": citation.title,
                "year": citation.year,
                "type": citation.source_type,
                "peer reviewed": citation.peer_reviewed,
                "metadata status": citation.metadata_status,
                "url": str(citation.url),
            }
            for citation in registries.citations
        ]
    )

