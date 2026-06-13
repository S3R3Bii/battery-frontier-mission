# Deployment and Automation

## GitHub Pages

The static mission-control website is deployed from `website/` by
`.github/workflows/pages.yml`.

The workflow regenerates:

- Phase 2 physics fixtures
- Phase 3 aviation fixtures
- Phase 4 dashboard method cards and manifest
- candidate evidence dossiers and Materials Project metadata appendix
- Phase 3.5/4.5 simulation campaign grids and summaries
- partner-facing dossier reports
- daily report artifacts
- `website/mission-control-data.json`

Then it uploads the `website/` directory with GitHub Pages actions.

If the first deployment does not publish automatically, open the repository on
GitHub and set:

`Settings -> Pages -> Build and deployment -> Source -> GitHub Actions`

## Daily Refresh

`.github/workflows/daily-report.yml` runs daily and on demand. It refreshes
reports, simulation campaign artifacts, candidate dossiers, and website data,
then commits generated outputs back to `main`.

## Metadata Refresh

`.github/workflows/metadata-ingestion.yml` runs weekly and on demand. It executes
metadata-only connector requests for:

- Carnegie Mellon eVTOL Battery Dataset article/file metadata
- Materials Project, when `MP_API_KEY` is configured
- NASA Technical Reports Server
- DOE OSTI

The generated manifests are source-discovery artifacts and source metadata. The
CMU eVTOL source is approved for trusted source snapshots, but its manifest is
not parsed measurement evidence. These manifests do not enable chemistry ranking.

## Simulation Campaign Refresh

`python -m battery_frontier.cli simulation-campaign` regenerates
`reports/simulations/` from configured mission assumptions and local model code.
The outputs are hashed and then consumed by the daily report and static website.

These artifacts are useful for showing how aviation requirements move under
route, payload, reserve, pack architecture, and degradation assumptions. They
are not measurements, validation records, certifiable aircraft designs, or
evidence that any candidate material can meet the requirements.

## CMU Measurement Refresh

The approved CMU eVTOL dataset should not be fully downloaded in CI by default.
Use explicit local commands for raw files:

```powershell
python -m battery_frontier.cli source-fetch-cmu-evtol --mode subset
python -m battery_frontier.cli verify-raw-snapshots
python -m battery_frontier.cli parse-cmu-evtol
```

Raw files are stored under `data/raw/approved/cmu_evtol_battery/` and are
ignored by Git. CI and Pages should prefer committed manifests, parsed
summaries, and website JSON instead of downloading the full archive.

## Partner Dossier Refresh

`python -m battery_frontier.cli partner-dossiers` writes latest partner reports
under `reports/partners/latest/` and creates archive snapshots under
`reports/partners/archive/` when the input signature changes.

## Required Secrets

No secrets are required for Pages, daily report, CMU eVTOL metadata, NASA NTRS,
or OSTI metadata workflows to complete. If `MP_API_KEY` is present, Pages, daily
report, and metadata refresh workflows also attach Materials Project
metadata-only discovery records to the candidate dossiers.

Materials Project metadata refresh requires:

- `MP_API_KEY`

Add it at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

If the secret is absent, workflows still complete. Candidate dossiers will still
be generated, but the Materials Project appendix will record
`blocked_requires_key`.

## Current Scientific Boundary

Automation refreshes the public dashboard and traceable artifacts. A
representative CMU subset can be parsed locally, but the project still does not
complete Phase 4 scientifically until comparable measurements, uncertainty,
pack-level boundaries, and external validation are available.
