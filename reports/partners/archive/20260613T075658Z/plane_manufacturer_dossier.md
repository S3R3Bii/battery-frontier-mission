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
- CMU measurement status: passed
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

- `simulation_campaign`: `9877ecc36bff9767d6b38a09f035751cda353c8a0b25393fa55d292b6ced900c` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `76054fd95003477cebe57237225d26d699dd2d712a117df2453451239150ec1d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `644395254906222ae137dc7a1fc08ce3003687c2face3d603847e9cc3c8776eb` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `cf1105e3bfd200442c36c378c85252fa2692d7a491d18817a484ed88b700fd75` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `cmu_measurement_summary`: `74407f2bb189cdecbb8705fa5a3abdee6fe3e16ff78ac591b6cc95cafc9e9fba` (`reports/measurements/cmu_evtol_measurement_summary.json`)
- `website_data`: `2a828e5af2bb92d979eac323082592dc7f8a875bb03efad6e0d11ab309956804` (`website/mission-control-data.json`)