# Mission-Control Website

This directory contains the polished static public dashboard surface for Phase 4.
It consumes `mission-control-data.json`, which is generated from the same
registry, artifact, report, and source-readiness data used by the scientific
dashboard.

```powershell
python -m battery_frontier.cli dashboard-artifacts
python -m battery_frontier.cli candidate-dossiers
python -m battery_frontier.cli daily-report
python -m battery_frontier.cli website-data
python -m http.server 8000
```

Open `http://localhost:8000/website/`.

The site intentionally shows an empty audited-measurement lane and keeps
chemistry ranking disabled. Fixture-only values are visible for system
demonstration and reproducibility checks, not as validated battery performance.
Candidate dossiers, including the hemp bast-fiber-derived graphitic carbon
lead, are displayed as proof-gap records only. The conceptual aircraft visual is
a mission reminder, not a blueprint or performance claim.
