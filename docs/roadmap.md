# Research Roadmap

## Phase 0: Scope and Targets - Complete

- Define system boundaries, evidence classes, target metrics, ranking gates,
  scenario semantics, and reproducibility rules.
- Exit: configuration validation and documentation agree.

## Phase 1: Schema and Literature Registry - Foundation Complete

- Build normalized schema, source/citation registers, claim structure,
  assumptions registry, chemistry-family queue, and ingestion contracts.
- Implemented locally: source readiness inventory, metadata-only connector
  scaffold, dry-run requests, optional metadata fetch paths for Materials
  Project, NASA NTRS, and OSTI, Materials Project credential gate, and immutable
  snapshot manifest writer.
- Exit: one licensed dataset can pass validation into an immutable snapshot.
- Remaining exit item: ingest the first approved external snapshot.

## Phase 2: Baseline Physics - Local Foundation Complete

- Expand full-reaction stoichiometry, voltage profiles, density bases,
  uncertainty propagation, cell bill-of-materials, and pack derating.
- Exit: reference calculations reproduce cited examples within declared tolerance.
- Implemented locally: reaction mass balance, explicit mass bases, weighted
  voltage profiles, deterministic positive intervals, density conversion,
  cell/pack bills of materials, reference fixtures, CLI output, and dashboard workbench.
- Remaining exit items: audit cited numerical examples, add correlated
  uncertainty methods, and validate architecture-specific bills of materials.

## Phase 3: Aviation Mission Simulator - Local Foundation Complete

- Add segment-based flight mechanics, payload-range iteration, power constraints,
  reserves, degradation, thermal behavior, and sensitivity analysis.
- Exit: benchmark against published aircraft studies without tuning away discrepancies.
- Implemented locally: taxi, climb, cruise, reserve, and descent segments;
  iterative battery-mass closure; energy, specific-power, and C-rate constraints;
  payload-range curves; sensitivity analysis; explicit infeasibility reporting;
  CLI artifacts; and dashboard views.
- Remaining exit items: benchmark against published aircraft studies, replace
  constant segment assumptions with validated profiles, and add thermal/power
  transients without concealing model-form uncertainty.

## Phase 4: Dashboard Prototype - Active

- Replace wireframe placeholders with audited records, traceable charts, and
  downloadable method cards.
- Implemented locally: mission-control status, evidence ledger, system-boundary
  energy chart, mission segment and sizing charts, payload-range and sensitivity
  views, source/citation audit pages, method cards, downloads, hash verification,
  static website data export, candidate evidence dossiers, Materials Project
  metadata appendix, a conceptual target-aircraft mission reminder, and a
  polished mission-control public surface.
- Remaining exit item: replace fixture-only scientific content with audited
  experimental measurements while retaining uncertainty and provenance.

## Phase 5: ML Screening

- Establish leakage-resistant baselines, uncertainty, calibration, and
  out-of-distribution checks before complex models.

## Phase 6: Multi-Objective Optimization

- Publish Pareto fronts across energy, safety, life, cost, abundance,
  manufacturability, and aviation mass penalties.

## Phase 7: Automated Reporting

- Connect scheduled ingestion, model runs, change detection, report generation,
  artifact signing, and publication review.

## Phases 8-10

- Public website, communication/video outputs based only on real artifacts, then
  external scientific review and contributor onboarding.
