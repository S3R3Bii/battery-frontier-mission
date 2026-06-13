# Phase 0 Scientific Scope

## Mission Question

Under explicit chemistry, cell, pack, aircraft, operating, and certification
assumptions, what energy-storage performance is physically plausible, what is
practically demonstrated, and what gap remains for defined aviation missions?

## System Boundaries

Values must be labeled at exactly one boundary:

| Boundary | Numerator | Denominator |
| --- | --- | --- |
| Active material | Reversible electrical energy | Mass of all active reactants included in the reaction basis |
| Cell | Deliverable cell energy | Complete cell mass |
| Pack | Deliverable pack energy | Cells plus pack structure, interconnects, controls, and pack thermal hardware |
| Installed storage | Deliverable storage energy | Pack plus external containment, cooling, and storage-specific integration |
| Aircraft useful | Propulsive-useful energy after operational penalties | Installed storage-system mass |
| Mission | Energy and power required for a defined route and reserve policy | Complete aircraft and mission assumptions |

Comparisons across different boundaries are prohibited unless a transparent
conversion is shown.

## Target Metrics

Every candidate assessment should ultimately include:

- specific energy and volumetric energy density at material, cell, and pack level
- usable depth of discharge, energy efficiency, power capability, and temperature window
- cycle and calendar life with stated end-of-life criterion
- thermal-runaway, dendrite, oxygen/water sensitivity, containment, and abuse risks
- manufacturing maturity, material abundance, toxicity, recyclability, and cost
- technology readiness and aviation-certification risk
- uncertainty interval, evidence class, source lineage, and reproducibility score

## Evidence Classes

| Class | Meaning | Public display rule |
| --- | --- | --- |
| Known experimental | Direct measurement with traceable methods | Show measurement conditions and uncertainty |
| Literature projection | Author-reported extrapolation or engineering projection | Show projection assumptions and source |
| Simulation estimate | Output produced by a versioned model | Show model/version/input hashes |
| Theoretical limit | Stoichiometric or physical upper bound | State excluded inactive mass and constraints |
| Speculative hypothesis | Testable but not adequately validated | Never place on a validated-performance leaderboard |

## Phase 0 Decision Gates

1. A value cannot be compared without a unit and system boundary.
2. A fact cannot be marked validated without at least one citation.
3. A numerical range cannot be ranked without uncertainty semantics.
4. A simulation cannot be public without input and code-version hashes.
5. A material-level result cannot be used as a pack result through naming alone.
6. A mission claim must state payload, range, reserve, degradation, thermal,
   propulsion, lift-to-drag, and battery-mass assumptions.

## Phase 0 Success Criteria

- Scope and boundaries are documented.
- Evidence taxonomy and ranking gates are executable.
- Initial metrics, assumptions, scenarios, and chemistry families validate.
- Equations are unit-tested and documented.
- Unknown performance fields remain explicitly unknown.

