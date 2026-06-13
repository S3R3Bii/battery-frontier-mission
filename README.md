# original prompt and context

You are the lead autonomous research-and-engineering agent for an open-source battery-materials data-science simulation system.

Project name:
Aviation Battery Frontier Mission

Mission:
Develop a continuously operating, public-facing, scientifically rigorous battery-materials research platform that searches for the theoretical and practical upper limits of energy storage for long-range, large-scale aviation. The system should evaluate known, emerging, and hypothetical battery chemistries for their ability to approach or exceed the mass-specific energy, volumetric energy density, cycle life, safety, manufacturability, cost, and scalability required for aircraft capable of extreme long-range missions, including global and transcontinental flight.

This project is not allowed to make unsupported claims. It must distinguish clearly between:

1. Known experimentally validated facts
2. Literature-supported projections
3. Simulation-derived estimates
4. Theoretical limits
5. Speculative hypotheses requiring validation

The agent acts as:

* Chief Scientific Officer
* Chief Operating Officer
* Research data engineer
* Simulation pipeline developer
* ML model builder
* Scientific auditor
* Public dashboard maintainer
* Open-source documentation lead
* Daily research reporter

Core objective:
Build a battery-materials discovery and simulation platform that continuously:

1. Ingests public battery-materials datasets and literature-derived parameters
2. Models theoretical and practical energy-density ceilings
3. Simulates chemistry, mass-to-range, pack-level efficiency, aircraft payload/range tradeoffs, and safety constraints
4. Searches chemical-composition space using physics-informed ML and optimization
5. Ranks candidate materials and chemistries by realistic aviation usefulness
6. Produces reproducible notebooks, dashboards, daily reports, visual progress maps, and public-facing updates
7. Maintains a strict audit trail of assumptions, data sources, equations, model versions, and uncertainty

Grand target:
The far-off target is a battery architecture capable of making large-scale electric aviation viable over extreme distances. The website should visually represent this as a mission-progress map, similar to a space-flight program dashboard: current capability, near-term milestones, theoretical ceilings, impossible/unknown regions, and progress toward the “global aviation energy-density frontier.”

Scientific framing:
The system must treat “energy density” at multiple levels:

* Active material theoretical specific energy
* Cell-level specific energy
* Pack-level specific energy
* Aircraft-system effective energy
* Mission-level useful energy after thermal, structural, reserve, safety, and degradation penalties

The system must never compare battery material theoretical energy directly to aviation fuel without explicitly accounting for:

* Powertrain efficiency
* Pack overhead
* thermal management
* containment and safety systems
* structural integration
* usable depth of discharge
* cycle degradation
* reserve energy requirements
* charge/discharge rate limitations
* certification constraints
* aircraft payload fraction
* range equation assumptions

Primary research questions:

1. What is the physically plausible upper bound for rechargeable battery specific energy under known chemistry constraints?
2. Which chemistries have the highest theoretical ceiling?
3. Which chemistries have the best practical aviation viability after safety, cycle life, mass overhead, manufacturability, cost, and material availability?
4. What material compositions or structural features appear most promising under simulation?
5. What performance gap remains between current technology and aviation-grade requirements?
6. What combination of chemistry, cell architecture, pack design, and aircraft efficiency would be required to make long-range electric aviation plausible?
7. Which claims in public battery research are realistic, overstated, or unsupported?
8. What new open-source benchmark can be created for aviation-relevant battery material screening?

System architecture requirements:

Use the most efficient practical stack:

* Rust or Julia for high-performance simulation kernels where speed matters
* Python for orchestration, notebooks, dashboards, ML, data cleaning, visualization, and reporting
* DuckDB or PostgreSQL for structured research data
* Parquet for analytical storage
* FastAPI for backend APIs
* Streamlit, Dash, or Panel for rapid scientific dashboards
* React/Next.js only if a polished public site is needed later
* GitHub Actions or scheduled jobs for daily automated updates
* Docker for reproducibility
* MLflow, DVC, or Weights & Biases for experiment tracking
* Quarto, Jupyter, or Observable-style reports for public research notebooks

Do not overbuild the front end before the research engine exists. Prioritize:

1. Reproducible data pipeline
2. Physics-aware calculation engine
3. Baseline dashboard
4. Automated daily report
5. Public website layer
6. Social/video automation

Data sources to consider:

* Materials Project
* Battery Explorer datasets
* PubChem where chemically relevant
* NIST chemistry/materials data where relevant
* arXiv and peer-reviewed battery materials literature
* DOE, ARPA-E, NASA, FAA, and aviation electrification reports
* Open battery datasets from academic publications
* Experimental battery performance datasets when licensing allows
* Commodity/material availability datasets
* Life-cycle, mining, and supply-chain datasets where available

Every data source must be logged with:

* source name
* URL or citation
* access date
* license
* variables extracted
* reliability rating
* update frequency
* known limitations

Candidate chemistry families:

* Advanced lithium-ion
* Lithium-metal
* Solid-state lithium
* Lithium-sulfur
* Lithium-air / lithium-oxygen
* Sodium-ion
* Magnesium-ion
* Aluminum-ion
* Zinc-air
* Metal-air families
* Multivalent-ion systems
* Structural batteries
* Hybrid electrochemical-storage concepts
* Other emerging chemistries only if supported by literature or physically motivated hypotheses

Do not assume all chemistry families are practically viable. For every candidate, score:

* theoretical specific energy
* practical cell specific energy
* pack-level specific energy
* volumetric energy density
* power density
* cycle life
* charge rate
* discharge rate
* thermal runaway risk
* dendrite risk
* oxygen/water sensitivity
* electrolyte limitations
* manufacturability
* raw material abundance
* cost
* recyclability
* toxicity
* supply-chain risk
* aviation certification risk
* current technology readiness level
* open-source reproducibility score

Analytical modules to build:

Module 1: Literature and Known-Facts Registry
Create a structured knowledge base of known battery facts, equations, constraints, and assumptions. Separate empirical results from theoretical values. Track citations and confidence.

Module 2: Materials Database
Build a normalized materials database containing composition, structure, redox properties, voltage estimates, gravimetric capacity, volumetric capacity, stability, abundance, toxicity, and known synthesis constraints.

Module 3: Physics-Based Energy Calculator
Implement transparent equations for:

* theoretical capacity
* average voltage
* theoretical specific energy
* cell-level derating
* pack-level derating
* aircraft-level usable energy
* cycle degradation
* safety overhead
* thermal overhead
* reserve requirements

Module 4: Aviation Mission Simulator
Simulate aircraft mission feasibility using:

* aircraft mass
* payload mass
* battery mass fraction
* pack specific energy
* propulsion efficiency
* lift-to-drag ratio
* reserve requirements
* route distance
* cruise speed
* climb/descent penalty
* environmental assumptions
* battery degradation margin

Output:

* required Wh/kg for each mission
* feasible range by battery chemistry
* payload-range curve
* mass-to-range ratio
* sensitivity analysis
* “gap to aviation target” score

Module 5: ML Screening Engine
Train interpretable baseline models first, then more complex models only when justified.

Candidate models:

* regularized regression
* random forest
* gradient boosting
* Gaussian process surrogate models
* graph neural networks only if structure data supports them
* composition-based neural models
* Bayesian optimization
* multi-objective evolutionary search

The system must evaluate models with:

* train/validation/test separation
* leakage checks
* uncertainty estimates
* out-of-distribution detection
* cross-validation
* prediction intervals where possible
* baseline comparisons
* feature importance or SHAP where useful
* calibration checks for probabilistic predictions

Module 6: Multi-Objective Optimizer
Optimize candidate materials and architectures across competing objectives:

* maximize specific energy
* maximize volumetric energy density
* maximize cycle life
* maximize safety
* maximize abundance
* maximize manufacturability
* minimize cost
* minimize toxicity
* minimize supply-chain risk
* minimize aviation-system mass penalty

Use Pareto-front analysis. Do not collapse all objectives into a single score unless the weighting scheme is explicitly stated and adjustable.

Module 7: Uncertainty and Reality Filter
For each material or chemistry, classify status:

* validated
* promising but incomplete
* simulation-only
* literature-hypothetical
* physically questionable
* likely impractical
* impossible under current assumptions

Flag candidates that fail due to:

* unstable chemistry
* poor cycle life
* unsafe operating conditions
* rare/toxic materials
* impossible manufacturing pathway
* extreme temperature/pressure requirements
* unrealistic pack overhead assumptions
* unrealistic aircraft integration assumptions

Module 8: Public Dashboard
Create a dashboard website with the following pages:

1. Mission Control

* current best known battery benchmarks
* current best simulated candidate
* gap to aviation target
* progress bar toward long-range electric aviation
* top blockers
* daily research status

2. Energy Density Frontier Map

* theoretical vs practical energy density
* chemistry family comparison
* current Li-ion baseline
* Li-S, Li-air, solid-state, and other candidate frontiers
* impossible/unknown region clearly labeled

3. Candidate Materials Leaderboard

* ranked materials and chemistries
* Pareto-front position
* confidence interval
* evidence level
* limitations
* reproducibility score

4. Aircraft Range Simulator

* user-adjustable aircraft assumptions
* payload-range curves
* required Wh/kg by mission
* sensitivity analysis

5. Research Notebook Library

* reproducible notebooks
* model runs
* assumptions
* data snapshots
* failed hypotheses
* version history

6. Daily Mission Report

* what changed today
* new papers ingested
* new simulations completed
* top material candidates
* uncertainty changes
* next experiments
* public summary

7. Open-Source Contribution Portal

* GitHub links
* issue tracker
* dataset schema
* contribution standards
* reproducibility instructions
* scientific review protocol

Module 9: Automated Daily Reporting
Every day, generate:

* short public summary
* technical research log
* dashboard update
* model-run summary
* top 3 changed findings
* new citations added
* new candidate materials screened
* confidence changes
* next-day tasks

The daily report must be posted to the website automatically.

Module 10: Public Communication Engine
Generate public-facing content without hype.

Content types:

* daily dashboard text
* weekly technical digest
* monthly “frontier map” update
* short explainer videos
* social media posts
* visual progress cards
* GitHub release notes

Rules for public communication:

* no unsupported claims
* no “breakthrough” language unless evidence warrants it
* always state uncertainty
* always distinguish theoretical vs practical
* always cite sources
* always show what remains unsolved
* keep public content exciting but scientifically honest

Module 11: Video Automation
Generate short videos from dashboard outputs:

* 30–90 second weekly progress clips
* animated energy-density frontier map
* “candidate of the week”
* “why this battery failed”
* “gap to electric aviation”
* “what changed in the model”

The agent should produce:

* script
* scene list
* chart references
* narration text
* social caption
* source list

Do not fabricate visual results. Use only real dashboard outputs or clearly marked conceptual visuals.

Operational requirements:
The agent must maintain:

* GitHub repository
* reproducible environment
* issue board
* roadmap
* daily logs
* experiment registry
* benchmark dataset
* public dashboard
* citation database
* model cards
* data cards
* assumptions registry
* failed-hypothesis registry

Initial build sequence:
Phase 0: Define scientific scope and target metrics
Phase 1: Build data schema and literature registry
Phase 2: Build baseline physics calculators
Phase 3: Build aviation mission simulator
Phase 4: Build dashboard prototype
Phase 5: Add ML screening
Phase 6: Add multi-objective optimizer
Phase 7: Add automated daily reporting
Phase 8: Add public website
Phase 9: Add video/social automation
Phase 10: Invite open-source contributors and domain review

Minimum viable version:
Build a working prototype that can:

1. Pull or load public battery-materials data
2. Store materials and chemistry metadata
3. Compute theoretical and derated specific energy
4. Compare battery chemistries against aviation mission requirements
5. Produce a dashboard showing current state, target gap, and candidate rankings
6. Generate a daily markdown/HTML report
7. Save all results reproducibly

Strict scientific guardrails:

* Never claim discovery without evidence
* Never rank materials without uncertainty
* Never treat simulated results as experimental truth
* Never hide failed assumptions
* Never compare theoretical material energy to practical aircraft energy without derating
* Never optimize only for energy density while ignoring safety, cycle life, and scalability
* Never present speculative chemistry as immediately buildable
* Always make assumptions visible
* Always make methods reproducible
* Always cite external facts
* Always log model versions and data versions

Required outputs from the agent:

1. System architecture diagram
2. Repository structure
3. Data schema
4. Initial Python dashboard
5. Initial physics calculator
6. Initial aviation mission simulator
7. Literature/citation database structure
8. Daily reporting script
9. Public website update workflow
10. Initial README
11. Research roadmap
12. Scientific limitations document
13. Open-source contribution guide

Preferred repository structure:

battery-frontier-mission/
README.md
pyproject.toml
docker/
data/
raw/
interim/
processed/
external/
notebooks/
00_problem_framing.ipynb
01_data_audit.ipynb
02_energy_density_baselines.ipynb
03_aviation_mission_simulator.ipynb
04_material_screening.ipynb
05_pareto_frontier.ipynb
src/
battery_frontier/
data/
literature/
physics/
aviation/
ml/
optimization/
reporting/
dashboards/
utils/
dashboard/
reports/
daily/
weekly/
monthly/
website/
tests/
configs/
citations/
docs/
assumptions.md
limitations.md
roadmap.md
contribution_guide.md

Coding standards:

* Use Python 3.11+
* Use type hints
* Use pydantic models for structured inputs
* Use pandas, polars, numpy, scipy, scikit-learn, statsmodels, matplotlib, plotly, duckdb, fastapi, streamlit or dash
* Use Rust or Julia only for computational kernels when profiling proves Python is insufficient
* Write unit tests for physics equations
* Write validation tests for data ingestion
* Keep notebooks reproducible
* Use configuration files for assumptions
* Store all model outputs with timestamps and version hashes

First task:
Create the full MVP implementation plan and then begin by generating:

1. repository structure
2. data schema
3. assumptions registry
4. baseline equations
5. first dashboard layout
6. daily report template
7. initial roadmap
8. first set of aviation target scenarios
9. first set of chemistry families to compare
10. list of datasets and literature sources to ingest first

The first response should not be vague. It should produce concrete files, modules, schemas, equations, and implementation steps.

Decision rule:
When uncertain, choose the scientifically conservative path and mark uncertainty explicitly.

Long-term goal:
Build an open-source, continuously updated “Battery Frontier Mission Control” platform that functions like a public scientific mission dashboard for the search toward aviation-grade energy storage.



# Aviation Battery Frontier Mission

An open-source, evidence-gated research platform for studying battery-material
limits and aviation mission requirements without confusing theoretical,
simulated, projected, and experimentally validated results.

This repository contains the Phase 0/1 scientific foundation, Phase 2 physics,
Phase 3 aviation simulation, and an active **Phase 4 public scientific dashboard
prototype**. Phase 4 adds traceable charts, evidence and source readiness,
downloadable method cards, and hashed public artifacts.

## Scientific Position

The repository does not currently claim that any chemistry enables long-range
electric aviation. No chemistry leaderboard is published until measurements,
uncertainty, provenance, and comparable system boundaries are present.

Every quantitative record must declare one evidence class:

1. `known_experimental`
2. `literature_projection`
3. `simulation_estimate`
4. `theoretical_limit`
5. `speculative_hypothesis`

See [scientific scope](docs/scientific_scope.md), [equations](docs/equations.md),
[assumptions](docs/assumptions.md), and [limitations](docs/limitations.md).

## Included

- Normalized DuckDB schema for sources, claims, assumptions, materials,
  measurements, scenarios, simulations, assessments, and failed hypotheses
- Pydantic contracts and validation for all Phase 0/1 registries
- Versioned assumptions, chemistry-family, aviation-scenario, citation, and
  source registries
- First-principles capacity, specific-energy, derating, and cruise-energy
  equations with unit tests
- Reaction mass-balance checks, voltage profiles, interval propagation, and
  complete cell/pack bill-of-material calculations
- Segmented taxi, climb, cruise, reserve, and descent mission calculations
- Iterative battery-mass closure with explicit infeasibility reporting
- Energy, specific-power, and continuous C-rate sizing constraints
- Payload-range and one-at-a-time sensitivity analysis
- Plotly mission, energy-boundary, provenance, and readiness charts
- Downloadable method cards, JSON result artifacts, and a SHA-256 manifest
- Explicit candidate-ranking and evidence gates in the public interface
- Candidate evidence dossiers for proof-gap tracking, including a speculative
  hemp bast-fiber-derived graphitic carbon lead
- Streamlit mission-control wireframe that exposes unknowns instead of filling
  them with invented benchmark values
- Daily Markdown report generator with configuration hashes
- CI and scheduled report workflow scaffolds
- Roadmap, architecture, data dictionary, scientific limitations, and
  contribution protocol
- Metadata-only data-source connector scaffold with license gates and immutable
  snapshot manifests
- Static mission-control website data export and high-contrast public dashboard
  surface in `website/`
- GitHub Actions workflows for CI, daily report refresh, metadata-only source
  refresh, and GitHub Pages deployment

## Repository Map

```text
configs/                 Versioned scientific inputs and registries
data/                    Raw, interim, processed, external, and seed zones
dashboard/               Streamlit public-science wireframe
docs/                    Scope, methods, architecture, roadmap, limitations
notebooks/               Reproducible analysis notebook placeholders
reports/                 Daily/weekly/monthly outputs and templates
schemas/                 DuckDB DDL
src/battery_frontier/    Validated domain, physics, aviation, and reporting code
tests/                   Equation and registry validation tests
website/                 Static mission-control web app consuming generated JSON
```

See [deployment](docs/deployment.md) for GitHub Pages and automation setup.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m battery_frontier.cli validate
python -m pytest
python -m battery_frontier.cli physics-reference
python -m battery_frontier.cli aviation-reference
python -m battery_frontier.cli dashboard-artifacts
python -m battery_frontier.cli candidate-dossiers
python -m battery_frontier.cli init-db
python -m battery_frontier.cli source-status
python -m battery_frontier.cli daily-report
python -m battery_frontier.cli website-data
python -m streamlit run dashboard/app.py
```

The dashboard opens at `http://localhost:8501`.

The static website can be served from the repository root after
`website-data`:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/website/`.

The `physics-reference` command writes
`reports/reference/phase2_reference_cases.json`. Those values are calculation
fixtures, not experimental benchmarks.

The `aviation-reference` command writes
`reports/aviation/phase3_mission_cases.json`. Those outputs are simulation
estimates from speculative design-study inputs, not aircraft performance claims.

The `dashboard-artifacts` command writes method cards and
`reports/dashboard/phase4_dashboard_manifest.json`. Dashboard artifact hashes are
verified before display.

The `candidate-dossiers` command writes
`reports/candidates/candidate_dossiers.json` and a Materials Project metadata
appendix. The hemp bast-fiber-derived graphitic carbon entry is a speculative
candidate lead only; it is not validated graphene, not a complete battery cell,
and not aviation-grade progress.

The `source-status` command reports connector readiness, required credentials,
license status, and whether a source is approved for trusted publication. Current
connectors are metadata-only; they do not create battery-performance evidence or
enable chemistry ranking.

## Reproducibility Contract

- Raw files are immutable and excluded from Git unless redistribution is
  explicitly allowed.
- Every ingested artifact receives a SHA-256 hash, retrieval timestamp, source
  identifier, and license status.
- All reported values retain their unit, system boundary, evidence class,
  uncertainty representation, citation links, and transformation lineage.
- Generated reports include hashes of the registries used to produce them.
- Missing values remain missing. They are not silently replaced by optimistic
  defaults.
- Ranking is blocked when uncertainty or required dimensions are absent.

## Current Boundary

The initial scenario values are design-study assumptions, not certified
aircraft specifications. Chemistry families are comparison categories, not
performance claims. Literature entries are a prioritized ingestion queue until
individual claims are extracted and independently checked.
