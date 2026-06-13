# Simulation Campaign Summary

> Parameter sweeps and what-if envelopes only. Not experimental validation,
> chemistry ranking, aircraft design, or certification evidence.

## Status

- Phase lane: 3.5/4.5
- Aviation grid rows: 270
- Feasible aviation rows: 92
- Infeasible aviation rows: 178
- Pack trade rows: 8748
- Pack trade rows above research ceiling: 5345
- Candidate envelopes: 11
- Audited measurements: 0
- Ranking enabled: False

## Limiting Constraints

```json
{
  "energy": 210,
  "specific_power": 60
}
```

## What Would Need To Be True

- Audited full-cell measurements need comparable system boundaries and uncertainty.
- Pack overhead, containment, thermal control, reserve, and degradation margins need explicit mass accounting.
- Mission feasibility needs published aircraft-study validation and transient power checks.
- Candidate material envelopes need cycle-life, safety, manufacturing, and source-lineage evidence before ranking.
- Hemp-derived graphitic carbon needs primary-paper audit and full-cell translation before any aviation claim.

## Guardrails

- Simulation rows cannot appear as audited measurements.
- Candidate envelopes cannot enable ranking.
- Hemp-derived graphitic carbon remains speculative electrode/scaffold context.