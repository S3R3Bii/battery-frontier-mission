from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping and reject empty or non-mapping documents."""
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return payload


def load_registry_file(filename: str) -> dict[str, Any]:
    payload = load_yaml(CONFIG_DIR / filename)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{filename} must contain a records list")
    return payload

