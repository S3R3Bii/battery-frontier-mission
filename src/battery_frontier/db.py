from __future__ import annotations

from pathlib import Path

from battery_frontier.config import PROJECT_ROOT


def initialize_database(database_path: Path | None = None) -> Path:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is required for `battery_frontier.cli init-db`. "
            "Install the project dependencies with `python -m pip install -e \".[dev]\"`."
        ) from exc

    target = database_path or PROJECT_ROOT / "data" / "battery_frontier.duckdb"
    target.parent.mkdir(parents=True, exist_ok=True)
    ddl = (PROJECT_ROOT / "schemas" / "001_initial.sql").read_text(encoding="utf-8")
    connection = duckdb.connect(str(target))
    try:
        connection.execute(ddl)
    finally:
        connection.close()
    return target
