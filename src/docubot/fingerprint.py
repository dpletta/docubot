"""File fingerprinting for staleness detection."""

from __future__ import annotations

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def fingerprint_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return file_sha256(path)
