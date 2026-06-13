# Materials Campaign

Phase 4.6 starts the first honest battery-material screening layer. It is a
hypothesis-screening system, not validated material discovery.

Run:

```powershell
python -m battery_frontier.cli materials-campaign
```

Generated artifacts:

- `reports/materials/material_screening_summary.json`
- `reports/materials/material_screening_summary.md`
- `reports/materials/material_candidate_cards.json`
- `reports/materials/material_frontier_gap.json`
- `reports/materials/materials_project_metadata_snapshot.json`

## Inputs

Material candidates live in
[`configs/material_candidates.yaml`](../configs/material_candidates.yaml).

Each candidate declares:

- material id and chemistry family
- role and system boundary
- evidence level and source type
- theoretical basis and measured basis, if any
- aviation relevance
- safety, abundance, supply, and manufacturability flags
- capacity and voltage assumptions, when an energy estimate is allowed
- derating and pack-overhead factors
- citation ids and source URLs
- whether it may appear in the audited lane

The current answer for audited-lane eligibility is `false` for all material
candidates.

## Screening Calculation

When both capacity and voltage assumptions exist:

```text
theoretical active-material Wh/kg = capacity_mAh_g * nominal_voltage_v
theoretical-only pack proxy = active-material Wh/kg * pack_overhead_factor
engineering-bounded pack proxy =
  active-material Wh/kg * cell_derating_factor * pack_overhead_factor
```

The output range around the engineering-bounded value is an assumption bracket,
not a statistical confidence interval.

Rows missing voltage or capacity are blocked from energy estimates. This is
intentional. An anode, scaffold, structural architecture, or supercapacitive
carbon cannot be converted into aviation pack Wh/kg without a full-cell system
boundary.

## Hemp/Bast-Fiber Carbon

Hemp/bast-fiber-derived graphene-like carbon is tracked as exploratory
natural-carbon architecture. It may be relevant as a conductive scaffold, anode
support, or hybrid supercapacitive component, but the repo does not claim:

- validated graphene structure
- full-cell battery performance
- pack-level energy density
- aviation duty-cycle suitability
- ranking evidence

The dashboard wording is:

> Exploratory carbon architecture; included for hypothesis tracking only. No
> validated aviation battery performance is claimed.

## Materials Project

If `MP_API_KEY` is present, the campaign fetches a small Materials Project
summary metadata query and writes it to
`reports/materials/materials_project_metadata_snapshot.json`.

Those records are computed material metadata only. They do not validate battery
performance, cycle life, safety, manufacturability, pack design, or aviation
usefulness. If the key is missing, the snapshot records `blocked_requires_key`
and the campaign still completes.

## Evidence Boundary

Material campaign rows are:

- simulation-only
- non-performance evidence
- non-audited
- non-ranking
- not DFT proof
- not experimental validation
- not pack proof
- not aircraft design
- not certification evidence

Phase 5 remains blocked until comparable audited measurements with uncertainty,
provenance, and system boundaries exist.
