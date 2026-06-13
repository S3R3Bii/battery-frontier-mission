# Initial Ingestion Queue

The machine-readable source is [`configs/data_sources.yaml`](../configs/data_sources.yaml).

Priority order:

1. Materials Project metadata through the supported API, after API terms and
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

- Materials Project reports `MP_API_KEY` as required before API execution.
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
