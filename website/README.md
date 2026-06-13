# Mission-Control Website

This directory contains the polished static public dashboard surface for Phase 4.
It consumes `mission-control-data.json`, which is generated from the same
registry, artifact, report, and source-readiness data used by the scientific
dashboard.

```powershell
python -m battery_frontier.cli dashboard-artifacts
python -m battery_frontier.cli candidate-dossiers
python -m battery_frontier.cli simulation-campaign
python -m battery_frontier.cli source-fetch-cmu-evtol --mode subset
python -m battery_frontier.cli parse-cmu-evtol
python -m battery_frontier.cli partner-dossiers
python -m battery_frontier.cli daily-report
python -m battery_frontier.cli website-data
python -m http.server 8000
```

Open `http://localhost:8000/website/`.

The site intentionally keeps chemistry ranking disabled. Parsed CMU eVTOL files,
when present, are shown as cell-level evidence only and not as pack-level
progress. Fixture-only values are visible for system demonstration and
reproducibility checks, not as validated battery performance. Candidate
dossiers, including the hemp bast-fiber-derived graphitic carbon lead, are
displayed as proof-gap records only. The conceptual aircraft visual is a mission
reminder, not a blueprint or performance claim.

The simulation campaign panels are generated from local assumptions and model
code. They map requirement envelopes, pack sensitivity, infeasible regions, and
candidate evidence gaps. They do not publish measurements or imply that a
candidate material has reached aviation-grade pack performance.

The current public data also includes manufacturer/propulsion context tables,
dataset triage, long-haul feasibility stress tests, and partner dossier links.
Those panels are source/context/reporting surfaces, not validation records.
