"""Repository path resolution."""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) to find git root or directory with .docubot."""
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / ".git").is_dir() or (path / ".docubot").is_dir():
            return path
    return current


def docubot_dir(repo_root: Path) -> Path:
    return repo_root / ".docubot"


def sessions_dir(repo_root: Path) -> Path:
    return docubot_dir(repo_root) / "sessions"


def manifest_path(repo_root: Path) -> Path:
    return docubot_dir(repo_root) / "manifest.json"


def config_path(repo_root: Path) -> Path:
    local = docubot_dir(repo_root) / "config.local.yaml"
    if local.is_file():
        return local
    return docubot_dir(repo_root) / "config.yaml"


def templates_dir(repo_root: Path) -> Path:
    return repo_root / "templates"


def schema_dir(repo_root: Path) -> Path:
    return docubot_dir(repo_root) / "schema"
