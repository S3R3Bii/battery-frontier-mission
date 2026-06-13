# Assumptions Registry

The machine-readable source is [`configs/assumptions.yaml`](../configs/assumptions.yaml).

Every assumption includes:

- stable identifier and version
- value, unit, category, and system boundary
- evidence class and lifecycle status
- uncertainty bounds or an explicit statement that uncertainty is not yet quantified
- citations when the value is externally supported
- rationale, sensitivity, owner, and review date

## Rules

1. Configuration values are not facts merely because they are machine-readable.
2. Scenario-design values are labeled `speculative_hypothesis`.
3. Mathematical constants are labeled `theoretical_limit`.
4. Defaults may support software operation but cannot silently become published
   benchmark values.
5. Changing an assumption requires a version increment and report provenance update.

