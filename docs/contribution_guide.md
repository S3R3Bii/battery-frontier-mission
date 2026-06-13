# Contribution Guide

## Scientific Changes

Every pull request that adds or changes a quantitative claim must include:

- source or DOI
- source license/redistribution status
- evidence class
- measurement or model conditions
- system boundary and units
- uncertainty representation
- extraction method and reviewer
- tests for equations or transforms

Do not add a chemistry ranking based on point estimates without uncertainty.
Do not convert cathode-only theoretical energy into a cell or pack claim.

## Engineering Changes

```powershell
python -m pip install -e ".[dev]"
python -m battery_frontier.cli validate
python -m pytest
python -m ruff check .
```

Raw licensed data should not be committed. Add a retrieval manifest and checksum
instead. Failed hypotheses and null results are valid contributions when methods
and assumptions are reproducible.

