# Initial Ingestion Queue

The machine-readable source is [`configs/data_sources.yaml`](../configs/data_sources.yaml).

Priority order:

1. Carnegie Mellon eVTOL Battery Dataset metadata snapshot from Figshare/KiltHub
   article `14226830`, approved under CC BY 4.0 for cell-level experimental
   aviation-duty-cycle evidence. Measurement-file ingestion is still a separate
   audit step.
2. Materials Project metadata through the summary API, with `MP_API_KEY`
   configured and records labeled as computed metadata until API terms and
   redistribution rules are recorded.
3. Battery Archive cycling data after dataset-level permission and license review.
4. NASA Technical Reports Server records relevant to electric-aircraft energy
   storage and mission analysis.
5. NIST Chemistry WebBook and PubChem identifiers/properties where their terms
   and variable fitness are confirmed.
6. Peer-reviewed review papers for chemistry-family constraints, followed by
   primary experimental papers for numerical measurements.

No automated download is enabled until a source has `license_status: approved`.

The dataset triage registry is
[`configs/dataset_candidates.yaml`](../configs/dataset_candidates.yaml). It now
tracks approved, review-required, and metadata-only candidates across battery
cycling, impedance, degradation, safety, aviation, propulsion, materials,
charging, and infrastructure categories. Rows in that registry are not ingested
measurements unless the license, system boundary, units, provenance, and parser
status have been approved.

## Connector Status

The repository includes metadata-only connector scaffolding for source readiness,
dry-run requests, and immutable snapshot manifests:

```powershell
python -m battery_frontier.cli source-status
python -m battery_frontier.cli source-dry-run --source datasource.nasa_ntrs
```

Current behavior:

- Carnegie Mellon eVTOL Battery Dataset has an approved CC BY 4.0 source record
  and an executable Figshare/KiltHub article-metadata connector. The connector
  fetches article and file metadata only. The separate CMU raw-snapshot command
  can download approved files, verify supplied MD5 and computed SHA-256 hashes,
  parse representative cell-level time-series and impedance CSVs, and write a
  measurement summary. Parsed CMU rows are cell-level evidence only; they are
  not pack-level proof and not candidate-ranking evidence.
- Materials Project uses `MP_API_KEY` and can execute a small metadata-only
  summary query when the key is present. Returned records are computed/material
  metadata, not cell, pack, cycle-life, safety, or aviation performance
  evidence.
- NASA NTRS and OSTI expose optional metadata fetch paths, but fetched records
  remain metadata-only until record-level review is complete.
- PubChem is represented as a dry-run property lookup because property-level
  provenance and attribution must be resolved before ingestion.
- Battery Archive, NIST Chemistry WebBook, and FAA reports remain manual-review
  sources until terms and record-level scope are recorded.

Snapshot manifests record source id, query, row count, request URL, retrieval
time, SHA-256 hash, license status, limitations, and whether trusted publication
is allowed. A manifest does not upgrade metadata into experimental battery
performance evidence.

## Candidate Metadata Appendix

`python -m battery_frontier.cli candidate-dossiers` writes a Materials Project
metadata appendix to `reports/source-metadata/`. It runs a small query plan
against element systems that can help find later audit targets for lithium,
sodium, multivalent, zinc-air, structural-carbon, and bio-derived carbon
candidate leads.

If `MP_API_KEY` is present, the command can fetch metadata automatically. If the
key is absent, the appendix records `blocked_requires_key` instead of creating a
partial trusted snapshot.

The carbon query is only a carbon-allotrope metadata proxy. It does not validate
hemp bast-fiber-derived graphitic carbon microstructure, electrochemical
performance, full-cell energy, safety, cycle life, manufacturing yield, or
aviation suitability.

## Material Candidate Registry

`configs/material_candidates.yaml` tracks material and architecture hypotheses
for Phase 4.6 screening. These records include source URLs, citation ids,
system boundaries, theoretical basis, safety/supply/manufacturing flags, and
whether an energy estimate is allowed.

The material registry is not a measurement dataset. Rows with missing full-cell
voltage or capacity assumptions are intentionally blocked from energy estimates.
Rows with estimates remain assumption-only diagnostics and cannot appear in
audited measurement, pack-proof, or ranking views.

`python -m battery_frontier.cli materials-campaign` writes
`reports/materials/` artifacts and a Materials Project metadata snapshot. If
`MP_API_KEY` is present, the command fetches a small metadata-only enrichment
query. If the key is absent, it records `blocked_requires_key`. In either case,
Materials Project rows remain computed material metadata, not battery
performance evidence.

## Automated Metadata Refresh

`.github/workflows/metadata-ingestion.yml` runs weekly and on demand. It executes
metadata-only requests for the approved CMU eVTOL Figshare article, Materials
Project when `MP_API_KEY` is configured, plus NASA NTRS and DOE OSTI, and writes manifests to
`reports/source-metadata/`.

These manifests are useful for finding candidate reports, benchmark studies, and
approved measurement archives. Materials Project manifests are useful for
computed-material discovery. CMU eVTOL manifests are approved source metadata,
but not parsed measurements or ranking inputs.

## CMU Measurement Commands

```powershell
python -m battery_frontier.cli source-fetch-cmu-evtol --mode metadata
python -m battery_frontier.cli source-fetch-cmu-evtol --mode subset
python -m battery_frontier.cli verify-raw-snapshots
python -m battery_frontier.cli parse-cmu-evtol --max-files 3 --max-rows-per-file 50000
python -m battery_frontier.cli measurement-summary
```

`--mode all` is available for the full archive, but raw files stay under
`data/raw/approved/cmu_evtol_battery/` and are ignored by Git. Do not enable full
archive download in CI without an explicit storage/runtime control.
