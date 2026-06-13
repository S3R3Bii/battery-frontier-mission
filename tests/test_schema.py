import sqlite3
from pathlib import Path

import pytest

from battery_frontier.schemas import VoltageSegmentInput


def test_initial_schema_is_parseable_sql() -> None:
    project_root = Path(__file__).resolve().parents[1]
    ddl = (project_root / "schemas" / "001_initial.sql").read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(ddl)
    finally:
        connection.close()


def test_voltage_segment_rejects_zero_voltage() -> None:
    with pytest.raises(ValueError):
        VoltageSegmentInput(
            label="invalid zero-voltage segment",
            capacity_fraction=1,
            average_voltage_v=0,
        )
