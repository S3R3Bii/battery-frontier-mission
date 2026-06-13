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
- Phase 3.5 requirement sweeps that vary route distance, payload, reserve,
  lift-to-drag ratio, propulsion efficiency, thermal availability, degradation,
  pack specific energy, pack specific power, and C-rate
- long-haul feasibility stress tests for short eVTOL, regional, 500 km,
  1000 km, 3000 km, and 6000+ km diagnostic mission profiles

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
python -m battery_frontier.cli simulation-campaign
```

`simulation-campaign` writes aviation requirement maps to
[`reports/simulations/aviation_requirement_grid.json`](../reports/simulations/aviation_requirement_grid.json)
and `.csv`, plus
[`reports/simulations/long_haul_feasibility.json`](../reports/simulations/long_haul_feasibility.json).
Those rows are simulation estimates and include explicit infeasible states. They
are useful for asking what would need to be true, not for claiming that a real
aircraft or battery meets those requirements.

## Remaining Validation Gate

Phase 3 is not complete until at least one published mission study is reproduced
using its stated aircraft mass, aerodynamic, reserve, battery, and efficiency
assumptions, with discrepancies reported rather than tuned away.
