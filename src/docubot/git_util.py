"""Git repository introspection."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(Exception):
    pass


def _run(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").is_dir()


def current_branch(repo_root: Path) -> str | None:
    if not is_git_repo(repo_root):
        return None
    try:
        return _run(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    except GitError:
        return None


def head_commit(repo_root: Path) -> str | None:
    if not is_git_repo(repo_root):
        return None
    try:
        return _run(repo_root, "rev-parse", "HEAD")
    except GitError:
        return None


def short_sha(sha: str, length: int = 7) -> str:
    return sha[:length] if sha else ""


@dataclass
class CommitInfo:
    sha: str
    short: str
    subject: str
    body: str


def parse_commit_message(message: str) -> tuple[str, str]:
    lines = message.splitlines()
    if not lines:
        return "", ""
    return lines[0], "\n".join(lines[1:]).strip()


CONVENTIONAL_RE = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
)

CHANGELOG_TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "docs": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "test": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
}


def conventional_changelog_type(subject: str) -> tuple[str, str]:
    """Return (section, clean_subject) from conventional commit subject line."""
    m = CONVENTIONAL_RE.match(subject)
    if not m:
        return "Changed", subject
    ctype = m.group("type").lower()
    section = CHANGELOG_TYPE_MAP.get(ctype, "Changed")
    return section, m.group("subject").strip()


def get_commit(repo_root: Path, sha: str) -> CommitInfo | None:
    if not is_git_repo(repo_root):
        return None
    try:
        fmt = _run(repo_root, "log", "-1", "--format=%H%n%B", sha)
    except GitError:
        return None
    parts = fmt.split("\n", 1)
    full_sha = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    subject, _ = parse_commit_message(body)
    return CommitInfo(sha=full_sha, short=short_sha(full_sha), subject=subject, body=body)


def commits_since(repo_root: Path, since_sha: str | None) -> list[CommitInfo]:
    if not is_git_repo(repo_root):
        return []
    if not since_sha:
        return []
    args = ["log", "--format=%H", f"{since_sha}..HEAD"]
    try:
        out = _run(repo_root, *args)
    except GitError:
        return []
    if not out:
        return []
    shas = out.splitlines()
    return [c for sha in shas if (c := get_commit(repo_root, sha))]


def changed_files_since(repo_root: Path, since_sha: str | None) -> list[str]:
    if not is_git_repo(repo_root):
        return []
    args = ["diff", "--name-only"]
    if since_sha:
        args.append(f"{since_sha}..HEAD")
    else:
        args.append("HEAD")
    try:
        out = _run(repo_root, *args)
    except GitError:
        return []
    return [line for line in out.splitlines() if line.strip()]


def dirty_files(repo_root: Path) -> list[str]:
    if not is_git_repo(repo_root):
        return []
    try:
        out = _run(repo_root, "status", "--porcelain")
    except GitError:
        return []
    files: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path)
    return files


def diff_name_only(repo_root: Path, ref: str = "HEAD") -> list[str]:
    if not is_git_repo(repo_root):
        return []
    try:
        out = _run(repo_root, "diff", "--name-only", ref)
        return [line for line in out.splitlines() if line.strip()]
    except GitError:
        return []
