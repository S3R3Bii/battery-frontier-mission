# Plane Manufacturer Dossier

> Factual partner brief. Simulations, metadata, and cell-level evidence are
> clearly separated from pack-level validation.

## Boundary

- Phase: 4.5 - dashboard and simulation automation active; experimental parsing is emerging
- Claim boundary: Do not treat metadata, fixtures, simulations, or cell-level data as pack-level validated aviation battery performance.
- Ranking enabled: False

## Current Signal

- Aircraft examples: 8
- Propulsion examples: 7
- Dataset candidates: 12
- CMU measurement status: blocked
- Long-haul infeasible cases: 4

## Feasibility Blockers

- No comparable audited pack-level aviation battery measurements are available.
- CMU eVTOL source is cell-level evidence and cannot prove pack sufficiency.
- Manufacturer examples are context records with mixed official/third-party boundaries.
- Long-haul feasibility remains simulation-only and expected-infeasible under current assumptions.
- Candidate ranking is blocked until uncertainty, safety, cycle-life, and system boundaries are audited.

## Collaboration Asks

- Provide aircraft-level mission assumptions with payload, reserve, pack mass, and thermal boundaries.
- Share non-proprietary pack-energy and power envelopes for reproducibility checks.
- Help validate mission profiles against aircraft design studies without tuning.

## Artifact Hashes

- `simulation_campaign`: `62e46a016653fea1fb558aad9d36032d5970d7ed83d14521322dd4ed04d8a07d` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `76054fd95003477cebe57237225d26d699dd2d712a117df2453451239150ec1d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `1e911bd65b71f8b27d0203687f4da89027780031ebecc8a8c8600c994fa3b7ae` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `8c04effffa0373d925b033f286c9981b5515eeb99c83899edfed535980c4b3e9` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `cmu_measurement_summary`: `9b93445ebd1e142ec1f87f0d838341e96440d459b062b280610b672851b7a076` (`reports/measurements/cmu_evtol_measurement_summary.json`)