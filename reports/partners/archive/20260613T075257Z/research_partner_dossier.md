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
- CMU measurement status: not_parsed
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

- `simulation_campaign`: `9877ecc36bff9767d6b38a09f035751cda353c8a0b25393fa55d292b6ced900c` (`reports/simulations/simulation_campaign_summary.json`)
- `long_haul_feasibility`: `76054fd95003477cebe57237225d26d699dd2d712a117df2453451239150ec1d` (`reports/simulations/long_haul_feasibility.json`)
- `candidate_dossiers`: `644395254906222ae137dc7a1fc08ce3003687c2face3d603847e9cc3c8776eb` (`reports/candidates/candidate_dossiers.json`)
- `cmu_raw_manifest`: `21991c67d8bc11290bbb8f7cccd95eabecc19f2edb66fba98df76169d3273b28` (`reports/measurements/cmu_evtol_raw_file_manifest.json`)
- `website_data`: `eb82ddfce247d9208a8cd197984d269be3c378e0d8db1c5d525ff0e4b4b6cdcd` (`website/mission-control-data.json`)