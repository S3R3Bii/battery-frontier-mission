# Method Card: Phase 3 Aviation Mission Model

## Purpose

Estimate mission energy, power, battery mass, payload-range behavior, and
constraint sensitivity using explicit constant-condition flight segments.

## Evidence Status

- All mission outputs: `simulation_estimate`
- Aircraft and battery fixtures: `speculative_hypothesis`
- Published-aircraft validation: not yet completed

## Segments

- taxi and ground load
- climb with drag and potential-energy rate
- steady level cruise
- explicit reserve loiter
- descent without regenerative-energy credit

## Sizing Constraints

- nominal mission energy at declared DoD, SoH, and thermal availability
- pack specific power
- continuous C-rate
- maximum takeoff mass
- maximum battery mass fraction

## Guardrails

- battery mass feeds back into aircraft mass until convergence
- non-convergence is retained as an infeasible result
- energy, power, and C-rate constraints are reported separately
- successful mathematical closure is not labeled aircraft feasibility

## Known Limitations

- constant mass and segment conditions
- no takeoff-roll, maneuver, wind, gust, or fault transient
- no thermal network or certification reserve interpretation
- no published-aircraft benchmark yet

## Reproduction

```powershell
python -m battery_frontier.cli validate
python -m battery_frontier.cli aviation-reference
```

## Result Artifact

- Path: `reports/aviation/phase3_mission_cases.json`
- SHA-256: `658c8e3fbfa22d7c73c2c841a0d7245d0b374f62852bcf10952d57829a57e306`
- Package version: `0.4.0`
