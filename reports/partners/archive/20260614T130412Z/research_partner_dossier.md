# Research Partner Dossier

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

- Contribute license-cleared datasets with schemas, units, uncertainty, and provenance.
- Help normalize impedance, capacity, temperature, and duty-cycle fields across datasets.
- Audit edge cases that could promote metadata or fixtures into measurement views.

## Artifact Hashes

- `simulation_campaign`: `766e58b21b853579fb24b61c9b0bf54ebc3eeaacb283fb1966a2bed245211d29` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `c799ca6825e7f5ba69f443f4faabfecd3377cd66bf6c3d496bf46dbd56f1256d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `6eca9b69f78fb55b308c71540cf87cdff2ec909c968e0ac9f03f38a664c4fae9` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `e5f999ee1a71983a79600b7f6400eb93b9609a6b51362a9b42552a4249f0daa4` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `cmu_measurement_summary`: `071929fc910141de21d2fb6e15a8a36af10e28b2620420c177490d496b25d222` (`reports/measurements/cmu_evtol_measurement_summary.json`)