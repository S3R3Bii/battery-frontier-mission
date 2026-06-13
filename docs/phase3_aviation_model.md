# Phase 3 Aviation Mission Model

The executable inputs are in
[`configs/segmented_mission_cases.yaml`](../configs/segmented_mission_cases.yaml).
Generated results are written to
[`reports/aviation/phase3_mission_cases.json`](../reports/aviation/phase3_mission_cases.json).

## Implemented Locally

- taxi and ground electrical load
- constant-rate climb with drag and potential-energy terms
- steady level cruise
- explicit reserve loiter
- descent with no regenerative-energy credit
- auxiliary loads in every airborne segment
- beginning-to-end battery availability penalties
- iterative battery mass and aircraft mass closure
- energy, pack-specific-power, and continuous C-rate constraints
- maximum takeoff mass and battery-fraction gates
- payload-range bisection
- one-at-a-time sensitivity analysis

## Reference Fixtures

### Regional Demonstrator

This case is configured to produce one converged local example. Its inputs are
illustrative and are not tied to a real aircraft. A successful closure means
only that the equations are internally consistent under those assumptions.

### Single-Aisle Stress Case

This case intentionally exposes divergent battery-mass feedback for a long-range
mission. Infeasibility is a valid scientific output and remains in the artifact.

## Evidence Status

Every output is `simulation_estimate` based on `speculative_hypothesis` inputs.
No result may be presented as demonstrated aircraft performance.

Run:

```powershell
python -m battery_frontier.cli aviation-reference
```

## Remaining Validation Gate

Phase 3 is not complete until at least one published mission study is reproduced
using its stated aircraft mass, aerodynamic, reserve, battery, and efficiency
assumptions, with discrepancies reported rather than tuned away.
