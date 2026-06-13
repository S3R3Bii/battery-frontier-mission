# Deployment and Automation

## GitHub Pages

The static mission-control website is deployed from `website/` by
`.github/workflows/pages.yml`.

The workflow regenerates:

- Phase 2 physics fixtures
- Phase 3 aviation fixtures
- Phase 4 dashboard method cards and manifest
- daily report artifacts
- `website/mission-control-data.json`

Then it uploads the `website/` directory with GitHub Pages actions.

If the first deployment does not publish automatically, open the repository on
GitHub and set:

`Settings -> Pages -> Build and deployment -> Source -> GitHub Actions`

## Daily Refresh

`.github/workflows/daily-report.yml` runs daily and on demand. It refreshes
reports and website data, then commits generated outputs back to `main`.

## Metadata Refresh

`.github/workflows/metadata-ingestion.yml` runs weekly and on demand. It executes
metadata-only connector requests for:

- NASA Technical Reports Server
- DOE OSTI

The generated manifests are source-discovery artifacts, not experimental battery
performance evidence. They do not enable chemistry ranking.

## Required Secrets

No secrets are required for the current Pages, daily report, NASA NTRS, or OSTI
metadata workflows.

Future Materials Project ingestion requires:

- `MP_API_KEY`

Add it at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

## Current Scientific Boundary

Automation refreshes the public dashboard and traceable artifacts. It does not
complete Phase 4 scientifically until audited external measurements with
licenses, system boundaries, uncertainty, and provenance are ingested.
