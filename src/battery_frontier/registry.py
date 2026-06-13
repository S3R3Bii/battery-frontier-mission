from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from battery_frontier.config import load_registry_file
from battery_frontier.schemas import (
    Assumption,
    AviationScenario,
    ChemistryFamily,
    Citation,
    DataSource,
    PhysicsReferenceCase,
    SegmentedMissionCase,
)

RecordT = TypeVar("RecordT", bound=BaseModel)


@dataclass(frozen=True)
class Registries:
    assumptions: list[Assumption]
    scenarios: list[AviationScenario]
    chemistries: list[ChemistryFamily]
    citations: list[Citation]
    data_sources: list[DataSource]
    physics_reference_cases: list[PhysicsReferenceCase]
    segmented_mission_cases: list[SegmentedMissionCase]

    def summary(self) -> dict[str, int]:
        return {
            "assumptions": len(self.assumptions),
            "scenarios": len(self.scenarios),
            "chemistry_families": len(self.chemistries),
            "citations": len(self.citations),
            "data_sources": len(self.data_sources),
            "physics_reference_cases": len(self.physics_reference_cases),
            "segmented_mission_cases": len(self.segmented_mission_cases),
        }


def _parse_records(filename: str, model: type[RecordT]) -> list[RecordT]:
    payload = load_registry_file(filename)
    records = [model.model_validate(record) for record in payload["records"]]
    identifiers = [record.id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{filename} contains duplicate IDs")
    return records


def _validate_citation_references(registries: Registries) -> None:
    known = {record.id for record in registries.citations}
    owners = [
        *registries.assumptions,
        *registries.scenarios,
        *registries.chemistries,
        *registries.data_sources,
        *registries.physics_reference_cases,
        *registries.segmented_mission_cases,
    ]
    missing = sorted(
        {
            citation_id
            for owner in owners
            for citation_id in owner.citation_ids
            if citation_id not in known
        }
    )
    if missing:
        raise ValueError(f"unknown citation references: {', '.join(missing)}")


def load_registries() -> Registries:
    registries = Registries(
        assumptions=_parse_records("assumptions.yaml", Assumption),
        scenarios=_parse_records("aviation_scenarios.yaml", AviationScenario),
        chemistries=_parse_records("chemistry_families.yaml", ChemistryFamily),
        citations=_parse_records("citations.yaml", Citation),
        data_sources=_parse_records("data_sources.yaml", DataSource),
        physics_reference_cases=_parse_records(
            "physics_reference_cases.yaml",
            PhysicsReferenceCase,
        ),
        segmented_mission_cases=_parse_records(
            "segmented_mission_cases.yaml",
            SegmentedMissionCase,
        ),
    )
    _validate_citation_references(registries)
    return registries
