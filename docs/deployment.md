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

- Materials Project, when `MP_API_KEY` is configured
- NASA Technical Reports Server
- DOE OSTI

The generated manifests are source-discovery artifacts, not experimental battery
performance evidence. They do not enable chemistry ranking.

## Simulation Campaign Refresh

`python -m battery_frontier.cli simulation-campaign` regenerates
`reports/simulations/` from configured mission assumptions and local model code.
The outputs are hashed and then consumed by the daily report and static website.

These artifacts are useful for showing how aviation requirements move under
route, payload, reserve, pack architecture, and degradation assumptions. They
are not measurements, validation records, certifiable aircraft designs, or
evidence that any candidate material can meet the requirements.

## Required Secrets

No secrets are required for Pages, daily report, NASA NTRS, or OSTI metadata
workflows to complete. If `MP_API_KEY` is present, Pages, daily report, and
metadata refresh workflows also attach Materials Project metadata-only discovery
records to the candidate dossiers.

Materials Project metadata refresh requires:

- `MP_API_KEY`

Add it at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

If the secret is absent, workflows still complete. Candidate dossiers will still
be generated, but the Materials Project appendix will record
`blocked_requires_key`.

## Current Scientific Boundary

Automation refreshes the public dashboard and traceable artifacts. It does not
complete Phase 4 scientifically until audited external measurements with
licenses, system boundaries, uncertainty, and provenance are ingested.
