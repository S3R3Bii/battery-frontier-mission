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

- `simulation_campaign`: `37f8955b96f42704b724fbb0b27ccba45f1f4329a5ae1591c751dde5ad0f4d70` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `c799ca6825e7f5ba69f443f4faabfecd3377cd66bf6c3d496bf46dbd56f1256d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `31ffced98c19d9df7c6ce92d8263d90e040f334e63815b9ad487e9b4ae77200b` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `e5f999ee1a71983a79600b7f6400eb93b9609a6b51362a9b42552a4249f0daa4` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `cmu_measurement_summary`: `071929fc910141de21d2fb6e15a8a36af10e28b2620420c177490d496b25d222` (`reports/measurements/cmu_evtol_measurement_summary.json`)