# Phase 1 Data Dictionary

The executable DDL is in [`schemas/001_initial.sql`](../schemas/001_initial.sql).

| Entity | Purpose |
| --- | --- |
| `data_sources` | Access, license, reliability, cadence, and limitations of upstream sources |
| `citations` | Stable bibliographic records |
| `claims` | Atomic scientific statements with evidence class and review state |
| `assumptions` | Versioned model/scenario inputs and uncertainty |
| `chemistry_families` | Comparison taxonomy without implied ranking |
| `materials` | Composition, structure, identifiers, and provenance |
| `measurements` | Conditioned values, units, boundaries, uncertainty, and citations |
| `aviation_scenarios` | Versioned mission-study inputs |
| `physics_reference_cases` | Versioned Phase 2 equation and boundary fixtures |
| `physics_reference_results` | Hashed outputs from reference calculations |
| `aviation_mission_cases` | Versioned segmented Phase 3 design studies |
| `aviation_mission_results` | Hashed mission, closure, range, and sensitivity outputs |
| `simulation_runs` | Code/input/environment provenance |
| `simulation_results` | Model outputs with unit, boundary, and uncertainty |
| `candidate_assessments` | Multi-objective evidence summaries |
| `failed_hypotheses` | Reproducible negative or invalidated findings |
| `artifacts` | Reports, charts, datasets, hashes, and publication state |

Required identifiers are strings so records can use readable, stable IDs. Dates
are ISO 8601. SI units are preferred internally; original units are retained in
source metadata.
