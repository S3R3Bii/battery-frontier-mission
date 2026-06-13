from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from battery_frontier import __version__
from battery_frontier.aviation.reference_cases import write_mission_results
from battery_frontier.config import PROJECT_ROOT
from battery_frontier.physics.reference_cases import write_reference_results
from battery_frontier.provenance import sha256_file
from battery_frontier.registry import load_registries


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    title: str
    artifact_type: str
    path: Path
    sha256: str
    evidence_status: str
    public_claim_boundary: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "title": self.title,
            "artifact_type": self.artifact_type,
            "path": self.path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": self.sha256,
            "evidence_status": self.evidence_status,
            "public_claim_boundary": self.public_claim_boundary,
        }


def _physics_method_card(result_path: Path) -> str:
    return f"""# Method Card: Phase 2 Physics Engine

## Purpose

Calculate transparent reaction-basis capacity, voltage-profile energy,
deterministic uncertainty intervals, volumetric conversion, and explicit cell
and pack bill-of-material boundaries.

## Evidence Status

- Faraday-law capacity: `theoretical_limit`
- Voltage-profile energy: `simulation_estimate` from declared inputs
- Cell and pack outputs: `simulation_estimate` from illustrative inputs
- Experimental validation: not yet completed

## Inputs

- `configs/physics_reference_cases.yaml`
- reaction stoichiometry and electron transfer
- declared mass basis
- voltage segments
- component masses and optional volumes
- utilization and efficiency factors

## Outputs

- theoretical specific capacity
- active-material specific and volumetric energy
- complete-cell specific and volumetric energy
- complete-pack specific and volumetric energy
- visible mass fractions and uncertainty intervals

## Guardrails

- reactant/product mass balance is checked
- product mass cannot be used as an input mass basis
- voltage fractions must sum to one
- cell and pack boundaries require explicit component mass
- fixture results cannot enter the validated chemistry leaderboard

## Known Limitations

- illustrative Li-S voltage and bill-of-material inputs
- deterministic bounds are not probability distributions
- no kinetics, rate, thermal transient, degradation, or abuse model
- no audited architecture-specific validation case

## Reproduction

```powershell
python -m battery_frontier.cli validate
python -m battery_frontier.cli physics-reference
```

## Result Artifact

- Path: `{result_path.relative_to(PROJECT_ROOT).as_posix()}`
- SHA-256: `{sha256_file(result_path)}`
- Package version: `{__version__}`
"""


def _aviation_method_card(result_path: Path) -> str:
    return f"""# Method Card: Phase 3 Aviation Mission Model

## Purpose

Estimate mission energy, power, battery mass, payload-range behavior, and
constraint sensitivity using explicit constant-condition flight segments.

## Evidence Status

- All mission outputs: `simulation_estimate`
- Aircraft and battery fixtures: `speculative_hypothesis`
- Published-aircraft validation: not yet completed

## Segments

- taxi and ground load
- climb with drag and potential-energy rate
- steady level cruise
- explicit reserve loiter
- descent without regenerative-energy credit

## Sizing Constraints

- nominal mission energy at declared DoD, SoH, and thermal availability
- pack specific power
- continuous C-rate
- maximum takeoff mass
- maximum battery mass fraction

## Guardrails

- battery mass feeds back into aircraft mass until convergence
- non-convergence is retained as an infeasible result
- energy, power, and C-rate constraints are reported separately
- successful mathematical closure is not labeled aircraft feasibility

## Known Limitations

- constant mass and segment conditions
- no takeoff-roll, maneuver, wind, gust, or fault transient
- no thermal network or certification reserve interpretation
- no published-aircraft benchmark yet

## Reproduction

```powershell
python -m battery_frontier.cli validate
python -m battery_frontier.cli aviation-reference
```

## Result Artifact

- Path: `{result_path.relative_to(PROJECT_ROOT).as_posix()}`
- SHA-256: `{sha256_file(result_path)}`
- Package version: `{__version__}`
"""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _embedded_provenance_status(path: Path) -> str:
    payload = _read_json(path)
    required = {
        "package_version",
        "config_sha256",
        "code_snapshot_sha256",
        "code_hashes",
        "claim_status",
    }
    return "verified_present" if required.issubset(payload) else "incomplete"


def generate_dashboard_artifacts(
    output_dir: Path | None = None,
) -> tuple[Path, list[ArtifactRecord]]:
    registries = load_registries()
    destination = output_dir or PROJECT_ROOT / "reports" / "dashboard"
    method_dir = destination / "method_cards"
    method_dir.mkdir(parents=True, exist_ok=True)

    physics_path = write_reference_results(registries.physics_reference_cases)
    aviation_path = write_mission_results(registries.segmented_mission_cases)

    physics_card_path = method_dir / "phase2_physics_method_card.md"
    aviation_card_path = method_dir / "phase3_aviation_method_card.md"
    physics_card_path.write_text(_physics_method_card(physics_path), encoding="utf-8")
    aviation_card_path.write_text(_aviation_method_card(aviation_path), encoding="utf-8")

    artifacts = [
        ArtifactRecord(
            artifact_id="artifact.phase2.results",
            title="Phase 2 physics reference results",
            artifact_type="json_results",
            path=physics_path,
            sha256=sha256_file(physics_path),
            evidence_status=_embedded_provenance_status(physics_path),
            public_claim_boundary="calculation fixtures; not experimental benchmarks",
        ),
        ArtifactRecord(
            artifact_id="artifact.phase3.results",
            title="Phase 3 aviation mission results",
            artifact_type="json_results",
            path=aviation_path,
            sha256=sha256_file(aviation_path),
            evidence_status=_embedded_provenance_status(aviation_path),
            public_claim_boundary="simulation estimates from speculative inputs",
        ),
        ArtifactRecord(
            artifact_id="artifact.phase2.method_card",
            title="Phase 2 physics method card",
            artifact_type="method_card",
            path=physics_card_path,
            sha256=sha256_file(physics_card_path),
            evidence_status="public_method_document",
            public_claim_boundary="documents equations, guardrails, and limitations",
        ),
        ArtifactRecord(
            artifact_id="artifact.phase3.method_card",
            title="Phase 3 aviation method card",
            artifact_type="method_card",
            path=aviation_card_path,
            sha256=sha256_file(aviation_card_path),
            evidence_status="public_method_document",
            public_claim_boundary="documents equations, guardrails, and limitations",
        ),
    ]

    manifest_path = destination / "phase4_dashboard_manifest.json"
    manifest = {
        "phase": "4",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "dashboard_status": "prototype with traceable local simulation artifacts",
        "experimental_measurements": 0,
        "chemistry_ranking_enabled": False,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path, artifacts

