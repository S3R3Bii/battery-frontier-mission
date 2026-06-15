# Method Card: Phase 2 Physics Engine

## Purpose

Calculate transparent reaction-basis capacity, voltage-profile energy,
deterministic uncertainty intervals, volumetric conversion, and explicit cell
and pack bill-of-material boundaries.

## Evidence Status

- Faraday-law capacity: `theoretical_limit`
- Voltage-profile energy: `simulation_estimate` from declared inputs
- Cell and pack outputs: `simulation_estimate` from illustrative inputs
- Experimental validation: not yet completed

## Inputs

- `configs/physics_reference_cases.yaml`
- reaction stoichiometry and electron transfer
- declared mass basis
- voltage segments
- component masses and optional volumes
- utilization and efficiency factors

## Outputs

- theoretical specific capacity
- active-material specific and volumetric energy
- complete-cell specific and volumetric energy
- complete-pack specific and volumetric energy
- visible mass fractions and uncertainty intervals

## Guardrails

- reactant/product mass balance is checked
- product mass cannot be used as an input mass basis
- voltage fractions must sum to one
- cell and pack boundaries require explicit component mass
- fixture results cannot enter the validated chemistry leaderboard

## Known Limitations

- illustrative Li-S voltage and bill-of-material inputs
- deterministic bounds are not probability distributions
- no kinetics, rate, thermal transient, degradation, or abuse model
- no audited architecture-specific validation case

## Reproduction

```powershell
python -m battery_frontier.cli validate
python -m battery_frontier.cli physics-reference
```

## Result Artifact

- Path: `reports/reference/phase2_reference_cases.json`
- SHA-256: `86de22d20d5b2cba83d2999c5d4fafe15638a4fdc85012fe025ded712dfd4717`
- Package version: `0.4.0`
