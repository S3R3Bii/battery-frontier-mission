# Battery Manufacturer Dossier

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

- Provide audited cell and pack data with uncertainty, test protocol, and mass boundary.
- Map safety, abuse, cycle-life, and thermal data to aviation-relevant duty cycles.
- Separate cell performance from module and pack overhead in reported evidence.

## Artifact Hashes

- `simulation_campaign`: `13bb445050699569d1883491c69f72c1b2dde805968b0aa659e29262786f4823` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `c799ca6825e7f5ba69f443f4faabfecd3377cd66bf6c3d496bf46dbd56f1256d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `a54cb25d5271703ede2d0f76b1931eaa598e70465d0a1784631b4be8d005d6d7` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `e5f999ee1a71983a79600b7f6400eb93b9609a6b51362a9b42552a4249f0daa4` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `cmu_measurement_summary`: `1c3882f98eae1b5cbf7d664252d08b48cde4d5a788b5cc3e6fe27b0be0915e3d` (`reports/measurements/cmu_evtol_measurement_summary.json`)