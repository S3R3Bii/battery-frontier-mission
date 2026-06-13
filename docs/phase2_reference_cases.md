# Phase 2 Reference Cases

The executable definitions are in
[`configs/physics_reference_cases.yaml`](../configs/physics_reference_cases.yaml).
Generated results are written to
[`reports/reference/phase2_reference_cases.json`](../reports/reference/phase2_reference_cases.json).

## Purpose

Reference cases test equations, units, system boundaries, and provenance. They
are not a chemistry leaderboard and do not establish practical performance.

## Lithium-Metal Capacity Identity

- Boundary: lithium electrode mass only
- Calculation: one electron per mole of lithium
- Purpose: reproduce Faraday's-law capacity and atomic-mass interval propagation
- Excludes: positive electrode, electrolyte, excess lithium, separator,
  collectors, casing, safety hardware, and pack overhead

## Lithium-Sulfur Boundary Demonstration

- Boundary 1: combined stoichiometric lithium and sulfur reactant mass
- Boundary 2: illustrative complete cell bill of materials
- Boundary 3: illustrative complete pack bill of materials
- Purpose: demonstrate how values decrease as inactive mass and efficiency
  factors enter the denominator and energy balance
- Evidence status: speculative fixture using an illustrative voltage profile and
  illustrative bills of materials

Run:

```powershell
python -m battery_frontier.cli physics-reference
```

Any future reference intended as literature validation must identify an audited
citation, reproduce its system boundary, and declare an acceptance tolerance.
