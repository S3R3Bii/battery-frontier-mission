from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.data.connectors import dry_run_source
from battery_frontier.registry import Registries, load_registries
from battery_frontier.schemas import ChemistryFamily
from battery_frontier.scientific_audit import evaluate_ranking_gate

DEFAULT_MP_ROWS = 2
DEFAULT_CANDIDATE_DIR = PROJECT_ROOT / "reports" / "candidates"
DEFAULT_MP_APPENDIX_PATH = (
    PROJECT_ROOT / "reports" / "source-metadata" / "materials_project_metadata_appendix.json"
)
DEFAULT_MP_APPENDIX_MARKDOWN_PATH = (
    PROJECT_ROOT / "reports" / "source-metadata" / "materials_project_metadata_appendix.md"
)

MATERIALS_PROJECT_QUERY_PLAN = (
    {
        "query_id": "mp.li_oxide",
        "query": "Li,O",
        "label": "lithium oxide and oxide electrolyte discovery",
        "candidate_ids": (
            "candidate.lithium_ion_intercalation",
            "candidate.lithium_metal",
            "candidate.lithium_oxygen",
        ),
    },
    {
        "query_id": "mp.li_sulfur",
        "query": "Li,S",
        "label": "lithium sulfur and sulfide discovery",
        "candidate_ids": ("candidate.lithium_sulfur",),
    },
    {
        "query_id": "mp.solid_electrolyte_sulfides",
        "query": "Li,P,S",
        "label": "lithium thiophosphate solid-electrolyte discovery",
        "candidate_ids": ("candidate.solid_state_lithium",),
    },
    {
        "query_id": "mp.lfp",
        "query": "Li,Fe,P,O",
        "label": "lithium iron phosphate and phosphate discovery",
        "candidate_ids": ("candidate.lithium_ion_intercalation",),
    },
    {
        "query_id": "mp.layered_oxides",
        "query": "Li,Ni,Mn,Co,O",
        "label": "layered oxide cathode discovery",
        "candidate_ids": ("candidate.lithium_ion_intercalation",),
    },
    {
        "query_id": "mp.sodium_oxides",
        "query": "Na,O",
        "label": "sodium oxide and sodium-ion host discovery",
        "candidate_ids": ("candidate.sodium_ion",),
    },
    {
        "query_id": "mp.multivalent_oxides",
        "query": "Mg,Al,Ca,O",
        "label": "multivalent oxide host discovery",
        "candidate_ids": ("candidate.multivalent",),
    },
    {
        "query_id": "mp.zinc_oxides",
        "query": "Zn,O",
        "label": "zinc oxide and air-cathode context discovery",
        "candidate_ids": ("candidate.zinc_air",),
    },
    {
        "query_id": "mp.carbon_allotropes",
        "query": "C",
        "label": "carbon allotrope metadata proxy; does not encode biomass origin",
        "candidate_ids": (
            "candidate.structural_battery",
            "candidate.hemp_bast_graphitic_carbon",
        ),
    },
)


@dataclass(frozen=True)
class CandidateSeed:
    candidate_id: str
    chemistry_id: str
    display_name: str
    candidate_type: str
    evidence_status: str
    system_boundary: str
    material_property_focus: tuple[str, ...]
    required_missing_evidence: tuple[str, ...]
    safety_unknowns: tuple[str, ...]
    cycle_life_unknowns: tuple[str, ...]
    manufacturing_unknowns: tuple[str, ...]
    next_evidence_actions: tuple[str, ...]
    notes: tuple[str, ...]
    citation_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata_query_ids: tuple[str, ...] = ()
    fixture_reference_ids: tuple[str, ...] = ()


GENERIC_REQUIRED_EVIDENCE = (
    "full-cell specific energy with complete active and inactive mass",
    "pack-specific energy with thermal, containment, controls, and reserve overhead",
    "uncertainty interval for energy, power, cycle life, and safety metrics",
    "source lineage, license status, and system boundary for every extracted value",
    "cycle-life protocol and failure criteria",
    "abuse, thermal-runaway, and containment evidence",
    "manufacturing route, yield assumptions, and scale constraints",
)

GENERIC_NEXT_ACTIONS = (
    "locate primary experimental records with full-cell boundaries",
    "record license and redistribution terms before publishing numerical claims",
    "extract uncertainty and test conditions before any ranking attempt",
    "map material evidence to cell, pack, and aircraft-mission boundaries",
)


def _default_seed(chemistry: ChemistryFamily) -> CandidateSeed:
    base_id = chemistry.id.removeprefix("chemistry.")
    query_ids = tuple(
        plan["query_id"]
        for plan in MATERIALS_PROJECT_QUERY_PLAN
        if f"candidate.{base_id}" in plan["candidate_ids"]
    )
    fixture_ids = (
        ("reference.lithium_sulfur_system_boundaries",)
        if chemistry.id == "chemistry.lithium_sulfur"
        else ()
    )
    return CandidateSeed(
        candidate_id=f"candidate.{base_id}",
        chemistry_id=chemistry.id,
        display_name=chemistry.name,
        candidate_type="chemistry_family_queue",
        evidence_status="registry_family_only_no_audited_measurements",
        system_boundary="chemistry family; no comparable cell or pack record ingested",
        material_property_focus=tuple(chemistry.required_metrics),
        required_missing_evidence=GENERIC_REQUIRED_EVIDENCE,
        safety_unknowns=(
            "abuse response not extracted",
            "thermal propagation and containment not quantified",
        ),
        cycle_life_unknowns=(
            "cycle protocol not normalized",
            "end-of-life criterion not audited",
        ),
        manufacturing_unknowns=(
            "scale route not audited",
            "quality/yield assumptions not recorded",
        ),
        next_evidence_actions=GENERIC_NEXT_ACTIONS,
        notes=(
            "This is a registry queue item, not a performance claim.",
            "Candidate remains unranked until audited measurements satisfy the evidence gate.",
        ),
        citation_ids=tuple(chemistry.citation_ids),
        source_ids=("datasource.materials_project",),
        metadata_query_ids=query_ids,
        fixture_reference_ids=fixture_ids,
    )


def _hemp_seed() -> CandidateSeed:
    return CandidateSeed(
        candidate_id="candidate.hemp_bast_graphitic_carbon",
        chemistry_id="chemistry.bio_derived_carbon_electrodes",
        display_name="Hemp bast-fiber-derived graphitic carbon nanosheets",
        candidate_type="speculative_material_hypothesis",
        evidence_status="speculative_literature_lead_not_audited_for_aviation_battery_use",
        system_boundary=(
            "bio-derived carbon electrode or conductive scaffold concept; not a complete "
            "battery cell, not a pack, and not an aircraft design input"
        ),
        material_property_focus=(
            "surface_area",
            "pore_size_distribution",
            "electrical_conductivity",
            "specific_capacitance",
            "full_cell_specific_energy",
            "thermal_stability",
            "precursor_variability",
            "carbonization_energy",
            "aviation_pack_specific_energy",
        ),
        required_missing_evidence=(
            "independent structural proof that the material is graphitic or graphene-like",
            "electrode-level data translated into a full-cell energy boundary",
            "comparison against conventional activated carbon under identical conditions",
            "battery-cell results, not only supercapacitor or half-cell behavior",
            "uncertainty intervals and batch-to-batch variability for hemp precursor lots",
            "carbonization, activation, washing, and binder/process mass and energy costs",
            "aviation-relevant safety, cycle-life, abuse, and pack-integration evidence",
        ),
        safety_unknowns=(
            "electrolyte compatibility not established for aviation battery packs",
            "thermal event behavior and off-gassing not characterized",
            "impurity sensitivity from biomass precursor not quantified",
        ),
        cycle_life_unknowns=(
            "cycle-life evidence is not normalized to comparable full cells",
            "calendar aging and high-rate degradation are unknown",
        ),
        manufacturing_unknowns=(
            "feedstock variability, activation yield, and graphitization energy are unknown",
            "quality control route for aviation-grade electrode material is not defined",
        ),
        next_evidence_actions=(
            "locate and audit primary hemp-derived carbon nanosheet papers",
            "separate supercapacitor claims from rechargeable battery evidence",
            "measure full-cell specific energy and uncertainty before ranking",
            "document precursor, processing, activation, washing, and yield boundaries",
        ),
        notes=(
            "The dashboard labels this as a speculative bio-derived carbon lead.",
            "It must not be called validated graphene or aviation-grade battery progress.",
            "Materials Project can only provide carbon allotrope metadata proxies; it cannot "
            "validate biomass-derived microstructure or electrochemical performance.",
        ),
        citation_ids=("lit.divya_nann_2020",),
        source_ids=("datasource.materials_project",),
        metadata_query_ids=("mp.carbon_allotropes",),
    )


def _chemistry_by_id(registries: Registries) -> dict[str, ChemistryFamily]:
    return {chemistry.id: chemistry for chemistry in registries.chemistries}


def _candidate_seeds(registries: Registries) -> list[CandidateSeed]:
    seeds = [_default_seed(chemistry) for chemistry in registries.chemistries]
    if "chemistry.bio_derived_carbon_electrodes" in _chemistry_by_id(registries):
        ids = {seed.candidate_id for seed in seeds}
        if "candidate.hemp_bast_graphitic_carbon" not in ids:
            seeds.append(_hemp_seed())
    return seeds


def build_materials_project_appendix(
    registries: Registries | None = None,
    *,
    rows: int = DEFAULT_MP_ROWS,
    execute_if_available: bool = False,
) -> dict[str, Any]:
    if rows <= 0:
        raise ValueError("rows must be positive")
    active_registries = registries or load_registries()
    queries: list[dict[str, Any]] = []
    for plan in MATERIALS_PROJECT_QUERY_PLAN:
        result = dry_run_source(
            active_registries,
            "datasource.materials_project",
            query=str(plan["query"]),
            rows=rows,
            execute=execute_if_available,
        )
        records = result.get("records", [])
        material_ids = [
            str(record["material_id"])
            for record in records
            if isinstance(record, dict) and record.get("material_id")
        ]
        queries.append(
            {
                "query_id": plan["query_id"],
                "query": plan["query"],
                "label": plan["label"],
                "candidate_ids": list(plan["candidate_ids"]),
                "status": result["status"],
                "executed": result["executed"],
                "record_count": result["record_count"],
                "material_ids": material_ids,
                "records": records,
                "request": result["request"],
                "license_status": result["license_status"],
                "trusted_publication": result["trusted_publication"],
                "ranking_evidence": result["ranking_evidence"],
                "metadata_only": result["metadata_only"],
                "limitations": result["limitations"],
                "error_message": result.get("error_message"),
            }
        )

    status_counts = Counter(query["status"] for query in queries)
    return {
        "artifact_type": "materials_project_metadata_appendix",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "source_id": "datasource.materials_project",
        "metadata_only": True,
        "trusted_publication": False,
        "ranking_evidence": False,
        "performance_evidence": False,
        "execute_if_available": execute_if_available,
        "requested_rows_per_query": rows,
        "query_count": len(queries),
        "record_count": sum(int(query["record_count"]) for query in queries),
        "status_counts": dict(sorted(status_counts.items())),
        "queries": queries,
        "limitations": [
            "Materials Project records are computed material metadata, not battery performance.",
            "Carbon-only metadata does not validate biomass-derived graphitic nanosheets.",
            "No record in this appendix is ranked or used as audited aviation battery evidence.",
        ],
    }


def _material_ids_by_candidate(appendix: dict[str, Any]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for query in appendix.get("queries", []):
        material_ids = [str(material_id) for material_id in query.get("material_ids", [])]
        for candidate_id in query.get("candidate_ids", []):
            grouped.setdefault(str(candidate_id), [])
            grouped[str(candidate_id)].extend(material_ids)
    return {key: sorted(set(values)) for key, values in grouped.items()}


def _ranking_candidate(seed: CandidateSeed) -> dict[str, Any]:
    return {
        "id": seed.candidate_id,
        "system_boundary": seed.system_boundary,
        "evidence_class": seed.evidence_status,
        "source_lineage": list(seed.source_ids),
        "pack_specific_energy_Wh_kg": None,
        "pack_specific_energy_uncertainty": None,
        "volumetric_energy_density_Wh_L": None,
        "cycle_life": None,
        "safety_assessment": None,
        "manufacturability_assessment": None,
    }


def build_candidate_dossiers(
    registries: Registries | None = None,
    *,
    materials_project_appendix: dict[str, Any] | None = None,
    execute_materials_project: bool = False,
    mp_rows: int = DEFAULT_MP_ROWS,
) -> dict[str, Any]:
    active_registries = registries or load_registries()
    appendix = materials_project_appendix or build_materials_project_appendix(
        active_registries,
        rows=mp_rows,
        execute_if_available=execute_materials_project,
    )
    seeds = _candidate_seeds(active_registries)
    chemistry_lookup = _chemistry_by_id(active_registries)
    material_ids_by_candidate = _material_ids_by_candidate(appendix)
    ranking_gate = evaluate_ranking_gate([_ranking_candidate(seed) for seed in seeds])

    dossiers: list[dict[str, Any]] = []
    for seed in seeds:
        chemistry = chemistry_lookup[seed.chemistry_id]
        missing_fields = ranking_gate.missing_by_candidate.get(seed.candidate_id, [])
        dossiers.append(
            {
                "id": seed.candidate_id,
                "display_name": seed.display_name,
                "chemistry_family_id": seed.chemistry_id,
                "chemistry_family": chemistry.name,
                "chemistry_family_evidence_class": chemistry.evidence_class.value,
                "chemistry_family_status": chemistry.status,
                "candidate_type": seed.candidate_type,
                "evidence_status": seed.evidence_status,
                "system_boundary": seed.system_boundary,
                "material_property_focus": list(seed.material_property_focus),
                "source_ids": list(seed.source_ids),
                "citation_ids": sorted(set([*seed.citation_ids, *chemistry.citation_ids])),
                "metadata_query_ids": list(seed.metadata_query_ids),
                "materials_project_material_ids": material_ids_by_candidate.get(
                    seed.candidate_id,
                    [],
                ),
                "fixture_reference_ids": list(seed.fixture_reference_ids),
                "audited_measurement_count": 0,
                "performance_evidence": False,
                "ranking_allowed": False,
                "ranking_blockers": missing_fields,
                "required_missing_evidence": list(seed.required_missing_evidence),
                "safety_unknowns": list(seed.safety_unknowns),
                "cycle_life_unknowns": list(seed.cycle_life_unknowns),
                "manufacturing_unknowns": list(seed.manufacturing_unknowns),
                "next_evidence_actions": list(seed.next_evidence_actions),
                "notes": list(seed.notes),
                "license_status": "not_approved_for_performance_publication",
                "display_guardrail": (
                    "Candidate dossier only. Do not interpret metadata, fixtures, or "
                    "speculative material leads as validated aviation battery performance."
                ),
            }
        )

    candidate_types = Counter(candidate["candidate_type"] for candidate in dossiers)
    summary = {
        "candidate_count": len(dossiers),
        "audited_measurement_count": 0,
        "ranking_enabled": ranking_gate.allowed,
        "ranking_gate_reason": ranking_gate.reason,
        "ranking_blocked_candidate_count": sum(
            bool(candidate["ranking_blockers"]) for candidate in dossiers
        ),
        "candidate_types": dict(sorted(candidate_types.items())),
        "materials_project_appendix": {
            "query_count": appendix["query_count"],
            "record_count": appendix["record_count"],
            "status_counts": appendix["status_counts"],
            "ranking_evidence": appendix["ranking_evidence"],
            "performance_evidence": appendix["performance_evidence"],
        },
        "hemp_candidate_id": "candidate.hemp_bast_graphitic_carbon",
    }
    return {
        "artifact_type": "candidate_evidence_dossiers",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "phase": "4",
        "ranking_enabled": ranking_gate.allowed,
        "ranking_gate_reason": ranking_gate.reason,
        "ranking_missing_by_candidate": ranking_gate.missing_by_candidate,
        "audited_measurements": 0,
        "summary": summary,
        "dossiers": dossiers,
        "materials_project_appendix": appendix,
        "limitations": [
            "Candidate dossiers are research triage records, not validated findings.",
            "Fixtures and metadata cannot appear as audited measurements.",
            "Hemp bast-fiber graphitic carbon remains a speculative candidate until "
            "primary papers and full-cell evidence are audited.",
        ],
    }


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _write_markdown_dossiers(payload: dict[str, Any], target: Path) -> None:
    lines = [
        "# Candidate Evidence Dossiers",
        "",
        "> These dossiers are research triage records. They are not chemistry rankings,",
        "> not audited measurements, and not aviation technology-readiness claims.",
        "",
        "## Summary",
        "",
        f"- Candidate dossiers: {payload['summary']['candidate_count']}",
        f"- Audited measurements: {payload['audited_measurements']}",
        f"- Ranking enabled: {payload['ranking_enabled']}",
        f"- Ranking gate: {payload['ranking_gate_reason']}",
        "- Materials Project appendix: "
        f"{payload['summary']['materials_project_appendix']['record_count']} metadata records",
        "",
        "## Dossiers",
        "",
    ]
    for dossier in payload["dossiers"]:
        lines.extend(
            [
                f"### {dossier['display_name']}",
                "",
                f"- Candidate id: `{dossier['id']}`",
                f"- Chemistry family: {dossier['chemistry_family']}",
                f"- Evidence status: `{dossier['evidence_status']}`",
                f"- Boundary: {dossier['system_boundary']}",
                f"- Audited measurements: {dossier['audited_measurement_count']}",
                f"- Ranking allowed: {dossier['ranking_allowed']}",
                "- Missing ranking fields: "
                + ", ".join(f"`{field}`" for field in dossier["ranking_blockers"]),
                "- Next evidence actions: "
                + "; ".join(dossier["next_evidence_actions"][:3]),
                "",
            ]
        )
    target.write_text("\n".join(lines), encoding="utf-8")


def _write_markdown_appendix(payload: dict[str, Any], target: Path) -> None:
    lines = [
        "# Materials Project Metadata Appendix",
        "",
        "> Metadata-only discovery output. This is not experimental battery evidence.",
        "",
        f"- Generated UTC: `{payload['generated_at_utc']}`",
        f"- Query count: {payload['query_count']}",
        f"- Record count: {payload['record_count']}",
        f"- Status counts: `{json.dumps(payload['status_counts'], sort_keys=True)}`",
        "",
        "| Query | Status | Records | Candidate links |",
        "| --- | --- | ---: | --- |",
    ]
    for query in payload["queries"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{query['query']}`",
                    f"`{query['status']}`",
                    str(query["record_count"]),
                    ", ".join(f"`{candidate_id}`" for candidate_id in query["candidate_ids"]),
                ]
            )
            + " |"
        )
    target.write_text("\n".join(lines), encoding="utf-8")


def write_candidate_dossiers(
    *,
    output_dir: Path | None = None,
    execute_materials_project: bool = False,
    mp_rows: int = DEFAULT_MP_ROWS,
) -> tuple[Path, Path, Path]:
    registries = load_registries()
    destination = output_dir or DEFAULT_CANDIDATE_DIR
    destination.mkdir(parents=True, exist_ok=True)
    appendix = build_materials_project_appendix(
        registries,
        rows=mp_rows,
        execute_if_available=execute_materials_project,
    )
    payload = build_candidate_dossiers(
        registries,
        materials_project_appendix=appendix,
        mp_rows=mp_rows,
    )
    appendix["payload_sha256"] = _sha256_payload(appendix)
    payload["materials_project_appendix_sha256"] = appendix["payload_sha256"]
    payload["payload_sha256"] = _sha256_payload(payload)

    json_path = destination / "candidate_dossiers.json"
    markdown_path = destination / "candidate_dossiers.md"
    appendix_path = DEFAULT_MP_APPENDIX_PATH
    appendix_markdown_path = DEFAULT_MP_APPENDIX_MARKDOWN_PATH
    appendix_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    appendix_path.write_text(
        json.dumps(appendix, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_markdown_dossiers(payload, markdown_path)
    _write_markdown_appendix(appendix, appendix_markdown_path)
    return json_path, markdown_path, appendix_path
