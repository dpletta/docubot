"""Documentation staleness checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docubot.config import Config
from docubot.git_util import changed_files_since, head_commit, is_git_repo
from docubot.state import Manifest


@dataclass
class StaleReport:
    stale: bool
    reason: str | None = None
    changed_files: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.changed_files is None:
            self.changed_files = []


def _matches_watch(path: str, watch_paths: list[str]) -> bool:
    from fnmatch import fnmatch

    normalized = path.replace("\\", "/")
    for pattern in watch_paths:
        p = pattern.replace("\\", "/")
        if fnmatch(normalized, p) or fnmatch(normalized, f"**/{p}"):
            return True
        # Directory prefix
        if p.endswith("/**"):
            prefix = p[:-3]
            if normalized.startswith(prefix + "/") or normalized == prefix:
                return True
    return False


def check_stale(repo_root: Path, config: Config, manifest: Manifest) -> StaleReport:
    if config.stale_check == "off":
        return StaleReport(stale=False)
    if not is_git_repo(repo_root):
        return StaleReport(stale=False, reason="not a git repository")

    head = head_commit(repo_root)
    if head and manifest.last_sync_commit == head:
        return StaleReport(stale=False)

    changed = changed_files_since(repo_root, manifest.last_sync_commit)
    watched = [f for f in changed if _matches_watch(f, config.watch_paths)]

    if not watched:
        return StaleReport(stale=False, changed_files=changed)

    return StaleReport(
        stale=True,
        reason=f"{len(watched)} watched file(s) changed since last doc sync",
        changed_files=watched,
    )
