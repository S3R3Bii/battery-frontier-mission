import builtins

import pytest

from battery_frontier.db import initialize_database


def test_init_db_missing_duckdb_error_is_actionable(monkeypatch, tmp_path) -> None:
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "duckdb":
            raise ImportError("duckdb missing for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="python -m pip install"):
        initialize_database(tmp_path / "battery_frontier.duckdb")
