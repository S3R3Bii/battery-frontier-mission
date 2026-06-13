# Initial Ingestion Queue

The machine-readable source is [`configs/data_sources.yaml`](../configs/data_sources.yaml).

Priority order:

1. Materials Project metadata through the summary API, with `MP_API_KEY`
   configured and records labeled as computed metadata until API terms and
   redistribution rules are recorded.
2. Battery Archive cycling data after dataset-level permission and license review.
3. NASA Technical Reports Server records relevant to electric-aircraft energy
   storage and mission analysis.
4. NIST Chemistry WebBook and PubChem identifiers/properties where their terms
   and variable fitness are confirmed.
5. Peer-reviewed review papers for chemistry-family constraints, followed by
   primary experimental papers for numerical measurements.

No automated download is enabled until a source has `license_status: approved`.

## Connector Status

The repository includes metadata-only connector scaffolding for source readiness,
dry-run requests, and immutable snapshot manifests:

```powershell
python -m battery_frontier.cli source-status
python -m battery_frontier.cli source-dry-run --source datasource.nasa_ntrs
```

Current behavior:

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

## Automated Metadata Refresh

`.github/workflows/metadata-ingestion.yml` runs weekly and on demand. It executes
metadata-only requests for Materials Project when `MP_API_KEY` is configured,
plus NASA NTRS and DOE OSTI, and writes manifests to
`reports/source-metadata/`.

These manifests are useful for finding candidate reports and benchmark studies.
Materials Project manifests are useful for computed-material discovery. They are
not approved external snapshots, experimental measurements, or ranking inputs.
