# Phase 4 Scientific Dashboard

The Streamlit dashboard is a public-science prototype, not a polished marketing
site. Its priority is traceability, visible uncertainty, and honest missing-data
states.

Phase 4 now also includes a static high-contrast mission-control website in
[`website/`](../website/) driven by
[`website/mission-control-data.json`](../website/mission-control-data.json). The
static site is the polished public surface; Streamlit remains the scientific
workbench.

The static site now also consumes candidate evidence dossiers from
[`reports/candidates/candidate_dossiers.json`](../reports/candidates/candidate_dossiers.json).
Those dossiers are proof-gap records. They preserve candidate ideas, including
hemp bast-fiber-derived graphitic carbon, without turning them into ranked or
validated battery claims.

## Pages

- **Mission Control**: phase readiness, evidence ledger, artifact verification,
  blockers, and registry counts
- **Physics Workbench**: reaction boundaries, energy derating, cell/pack mass
  allocation, uncertainty, and downloads
- **Energy Density Frontier**: illustrative system-boundary path plus chemistry
  evidence readiness; no cross-chemistry ranking
- **Candidate Evidence Gate**: required fields and explicit ranking block
- **Aviation Mission Simulator**: segment energy/power, sizing constraints,
  payload-range, sensitivity, feasibility reasons, and downloads
- **Evidence & Sources**: source licenses, ingestion state, citation audit, and
  evidence ledger
- **Methods & Artifacts**: SHA-256 verification, method cards, result files, and
  dashboard manifest
- **Daily Mission Report**: current research status and downloadable report

## Static Website

Generate the website data after refreshing artifacts:

```powershell
python -m battery_frontier.cli dashboard-artifacts
python -m battery_frontier.cli candidate-dossiers
python -m battery_frontier.cli daily-report
python -m battery_frontier.cli website-data
python -m http.server 8000
```

Open `http://localhost:8000/website/`.

The primary website chart shows:

- audited measurement lane: currently empty
- local physics fixture lane: theoretical or simulation-only values
- mission pack-input lane: configured Phase 3 inputs, not validated
  aviation requirements
- unknown/unvalidated region: clearly labeled
- candidate dossier rail: required proof, blockers, and metadata-only source
  context
- conceptual target aircraft rail: mission reminder only, not a design claim

## Reproduction

```powershell
python -m battery_frontier.cli validate
python -m battery_frontier.cli physics-reference
python -m battery_frontier.cli aviation-reference
python -m battery_frontier.cli dashboard-artifacts
python -m battery_frontier.cli candidate-dossiers
python -m streamlit run dashboard/app.py
```

Open `http://localhost:8501`.

## Scientific Guardrails

- chemistry ranking remains disabled with zero audited measurements
- theoretical, simulated, speculative, and missing evidence are visibly distinct
- phase progress describes software implementation only
- every downloadable scientific result has a SHA-256 hash
- method cards state purpose, inputs, outputs, guardrails, and limitations
- infeasible mission results remain visible
- static website progress visuals do not represent technology readiness
- hemp bast-fiber graphitic carbon is displayed as a speculative material lead,
  not as validated graphene, cell evidence, or pack evidence

## Remaining Phase 4 Exit Gate

The interface is operational, but Phase 4 is not scientifically complete until
audited experimental records with comparable boundaries, uncertainty, source
lineage, and licensing status are available for display.
