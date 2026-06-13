from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_files(paths: list[Path], root: Path | None = None) -> dict[str, str]:
    output: dict[str, str] = {}
    for path in sorted(paths):
        key = str(path.relative_to(root)) if root else str(path)
        output[key.replace("\\", "/")] = sha256_file(path)
    return output

