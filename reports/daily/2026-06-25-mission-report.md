# Daily Mission Report - 2026-06-25

> Phase: 4/4.5 scientific dashboard and simulation automation active
>
> Evidence status: CMU cell-level subset parser status is blocked.
> Chemistry performance ranking is intentionally disabled.

## Public Summary

The Phase 0/1 scientific foundation, Phase 2 physics engine, and Phase 3 mission
model are established locally. Phase 4 now publishes traceable charts, evidence
readiness, downloadable method cards, and hashed result artifacts. A CMU
cell-level subset can now be parsed when present. Experimental chemistry
rankings remain blocked because pack-level comparable evidence is not available.

## What Changed

- Registered assumptions: 12
- Registered aviation design-study scenarios: 4
- Registered chemistry families awaiting comparable evidence: 10
- Candidate evidence dossiers: 11
- Registered citations and source records: 12
- Registered upstream data sources: 8
- Registered aircraft systems: 8
- Registered propulsion systems: 7
- Dataset candidates queued for review: 12
- Material candidates in hypothesis screening: 14
- Registered Phase 2 reference calculations: 2
- Registered Phase 3 mission calculations: 2
- Phase 3 fixtures feasible under configured assumptions: 1
- Phase 4 downloadable artifacts: 4
- Parsed experimental cell-level files: 0
- CMU measurement quality status: blocked
- Simulations completed: 2
- Simulation campaign aviation grid rows: 270
- Simulation campaign pack trade rows: 8748
- Long-haul stress-test rows: 6
- Materials campaign status: generated
- Materials screened: 14
- Highest theoretical-only pack estimate: 17344.8 Wh/kg
- Highest engineering-bounded pack estimate: 1214.136 Wh/kg
- Partner dossiers generated: 5
- Candidate rankings changed: 0

## Top Three Changed Findings

1. Physics and aviation outputs now have public method cards and manifest hashes.
2. Dashboard charts retain evidence class, system boundary, assumptions, and limitations.
3. Source readiness and missing experimental evidence are visible instead of
   being replaced with an unsupported chemistry leaderboard.
4. Candidate dossiers preserve promising leads, including hemp bast-fiber-derived
   graphitic carbon, without upgrading them into validated measurements.
5. The simulation campaign now maps aviation requirements, pack architecture
   penalties, candidate envelopes, and infeasible regions without creating
   experimental evidence.
6. The materials campaign now screens material hypotheses against aviation
   requirement bands while keeping all results out of audited and ranking lanes.

## Evidence Ledger

| Finding | Evidence class | Boundary | Uncertainty | Citation or run |
| --- | --- | --- | --- | --- |
| Faraday-law capacity equation implemented | theoretical_limit | reaction basis | constant plus declared mass basis | source code and tests |
| Cruise mechanical-energy equation implemented | theoretical_limit | mission model | model-form uncertainty not yet quantified | source code and tests |
| Aviation scenarios registered | speculative_hypothesis | mission | scenario note and sensitivity ranges | no external claim |
| Phase 2 calculation fixtures | theoretical or speculative | reaction/cell/pack | deterministic intervals | source code and tests |
| Phase 3 segmented mission fixtures | simulation_estimate | aircraft mission | sensitivity studies, not confidence intervals | source code and tests |
| Phase 4 dashboard artifacts | public method and result artifacts | dashboard | SHA-256 integrity checks | dashboard manifest |
| CMU eVTOL representative subset | known_experimental | cell-level | parser status: blocked; pack evidence: false | CMU raw and measurement manifests |

## Source Readiness

```json
{
  "approved_metadata_snapshot_ready": 1,
  "blocked_by_license_review": 2,
  "metadata_ready": 1,
  "planned": 4
}
```

## Connector Readiness

- Metadata connectors with optional execution paths: 4
- Sources approved for trusted published snapshots: 1
- Materials Project status: requires `MP_API_KEY` before API execution.
- CMU eVTOL battery status: approved CC BY 4.0 cell-level experimental source;
  raw snapshot status: {'already_present': 3, 'downloaded': 41};
  parsed measurement status: blocked.
- NASA NTRS and OSTI status: metadata connectors are available; records remain
  metadata-only until reviewed.

## Dashboard Artifact Hashes

- `artifact.phase2.results`: `170b38a64574b6aaabe0438719109a92c3a352c8881e6daa512fe0fe245ec532`
- `artifact.phase3.results`: `c9ea6f7443600d0e4dfd0548f98946850a29c8363428441e876ab438e44b1b65`
- `artifact.phase2.method_card`: `b0c41dc5ddefda52d0b8c11477829ef097fd588163171f85b4e7c468be547a4c`
- `artifact.phase3.method_card`: `ed5128678afb06cec75a6041ed3381798028edffde2866940fc289b1a8c3554a`

## Assumption Changes

Phase 2 and Phase 3 fixtures remain versioned separately from empirical
measurements. Phase 4 displays those labels and verifies downloadable artifact
hashes; it does not upgrade simulations into facts.

## Candidate Screening

- Candidate dossiers: 11
- Ranking enabled: False
- Ranking gate: Ranking blocked: required comparable evidence or uncertainty is missing.
- Candidates blocked by missing ranking fields: 11
- Materials Project metadata records linked as discovery context: 18
- Hemp bast-fiber graphitic carbon status: speculative material lead only; no
  audited full-cell, pack, cycle-life, safety, or aviation performance evidence.

Required experimental, uncertainty, safety, cycle-life, manufacturing, and
source-lineage fields are not yet populated for ranking.

## Simulation Campaign

- Campaign status: generated
- Simulation-only outputs: True
- Aviation grid rows: 270
- Feasible aviation rows: 92
- Infeasible aviation rows: 178
- Pack trade-space rows: 8748
- Pack rows above research ceiling: 5345
- Candidate envelopes: 11
- Long-haul stress tests: 6
- Long-haul infeasible cases: 4
- Pack-level evidence created: no
- Ranking enabled by simulations: False

```json
{
  "energy": 210,
  "specific_power": 60
}
```

## Materials Campaign

- Campaign status: generated
- Simulation-only outputs: True
- Material candidates: 14
- Energy-estimated candidates: 10
- Energy-blocked candidates: 4
- Frontier gap rows: 84
- Highest theoretical-only pack estimate: 17344.8 Wh/kg
- Highest engineering-bounded pack estimate: 1214.136 Wh/kg
- Hemp/bast-fiber carbon present: True
- Materials Project status: fetched
- Ranking enabled by materials screening: False

Material screening values are assumptions for hypothesis triage. They are not
validated material discovery, DFT results, full-cell measurements, pack proof,
or aircraft performance evidence.

## Uncertainty and Reality Filter

Unknown performance remains unknown. Chemistry-family records identify required
metrics and known research constraints but contain no comparative scores.

## Failed or Rejected Hypotheses

None logged yet. The normalized schema includes a failed-hypothesis registry so
negative results remain public and reproducible.

## Next Work

1. Download the full CMU eVTOL archive when runtime is acceptable and keep it out of Git.
2. Parse more CMU cell-level files and audit units, timestamps, capacity,
   current sign convention, temperature, impedance, and system boundary.
3. Normalize parsed cell summaries into local DuckDB/Parquet storage.
4. Audit a published full-reaction reference and define acceptance tolerance.
5. Reproduce one published aviation mission study without tuning discrepancies away.
6. Add segment power and thermal transients with visible model-form uncertainty.
7. Convert review-required dataset candidates into approved snapshots only after license review.

## Reproducibility

- Package version: `0.4.0`
- Code snapshot SHA-256: `706c4e26d6356f1dbe807902cfadb02fb1d7ef3e0cb7695648a65472186cb96e`
- Python: `3.11.15`
- Platform: `Linux-6.17.0-1018-azure-x86_64-with-glibc2.39`
- Generated UTC: `2026-06-25T13:26:25.207966+00:00`
- Configuration hashes:
- `configs/aircraft_systems.yaml`: `f28336c50e7777958acb96b0f0b48298b984c9c27a86c1f3cb258b35c6d10e23`
- `configs/assumptions.yaml`: `63c51f3fbd90e4582d5b334b1552c006d63b89576d01f7f903ba1763ffbf45b8`
- `configs/aviation_scenarios.yaml`: `a3b15ca13fefc5f51ae237dbcf40d335c1dab630c8100b9bd1f44c4020989cce`
- `configs/chemistry_families.yaml`: `954d118a81f8a374b4081ac075dc3491ef6a848547ff3ae8c82f066c40f5cfd8`
- `configs/citations.yaml`: `3f44cba05cde92e10ebf081dcef86ba52f09bf1eb729e7126d6b0f7d6b0beb1e`
- `configs/data_sources.yaml`: `fa92b32d8cb43470c4346516a4072ad0afc2b83a5428faaa42965b23f76b6c67`
- `configs/dataset_candidates.yaml`: `e0d85c0e6f3e29a932152ec31e46d0cb0afce48eae71ac7283adc4dffc12126b`
- `configs/material_candidates.yaml`: `dfbce83c3986fba036d50effec69a81fd508fe1eabdd80adda01abbb96720569`
- `configs/physics_reference_cases.yaml`: `8451321c4c1383b1258ebb06f0674030caac37244eab5efac43b100be90d7c10`
- `configs/propulsion_systems.yaml`: `5bc9675209d8465c035af1f9378ad16265b58b733a3ef9d23a92e43ad31afd4f`
- `configs/segmented_mission_cases.yaml`: `6c75580c122655c6fe3b6b9292c2e9ebfe40fa4163772d73d830307d2a7753b2`
- Dashboard manifest: `reports/dashboard/phase4_dashboard_manifest.json`
- Candidate dossier artifact: `reports/candidates/candidate_dossiers.json`
- Candidate dossier SHA-256: `5eb727e951d2f9937f6eb9e22ef97ddfbe69ffeaeb27567140cd106b40b45744`
- Simulation campaign artifact: `reports/simulations/simulation_campaign_summary.json`
- Simulation campaign SHA-256: `7c4c0ae330d2a5ff3a9053e6805fb32050e0934577ab933b294c0d82a3cedbb5`
- Materials campaign artifact: `reports/materials/material_screening_summary.json`
- Materials campaign SHA-256: `c0527257b8cfcd23c28cac7a3cf2801a069d140acfafab914ecf3d50e766ef38`
- CMU raw manifest SHA-256: `e5f999ee1a71983a79600b7f6400eb93b9609a6b51362a9b42552a4249f0daa4`
- CMU measurement summary SHA-256: `071929fc910141de21d2fb6e15a8a36af10e28b2620420c177490d496b25d222`
- Partner dossier manifest SHA-256: `f1cbae8553433b5fd6bc9c3011fcfa585a836bccf4ddec939361f1700092f30b`

## Limitations

This Phase 4/4.5 report may include parsed CMU cell-level evidence, but it
contains no audited pack-level battery performance or validated aircraft mission
record. Scenario outputs are unsuitable for design, procurement, investment,
operations, or certification decisions.
