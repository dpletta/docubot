"""CHANGELOG.md maintenance (Keep a Changelog)."""

from __future__ import annotations

import re
from pathlib import Path

from docubot.git_util import CommitInfo, conventional_changelog_type, short_sha

UNRELEASED_HEADER = "## [Unreleased]"
SECTION_HEADERS = ("### Added", "### Changed", "### Fixed", "### Removed", "### Security")


def ensure_changelog(path: Path, template_text: str | None = None) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if template_text:
        path.write_text(template_text, encoding="utf-8")
    else:
        path.write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n",
            encoding="utf-8",
        )


def _ensure_unreleased(text: str) -> str:
    if UNRELEASED_HEADER not in text:
        if "# Changelog" in text:
            return text.replace("# Changelog", f"# Changelog\n\n{UNRELEASED_HEADER}", 1)
        return f"# Changelog\n\n{UNRELEASED_HEADER}\n\n" + text
    return text


def _insert_under_section(text: str, section: str, line: str) -> str:
    text = _ensure_unreleased(text)
    header = f"### {section}"
    if header not in text:
        # Add section after [Unreleased]
        idx = text.index(UNRELEASED_HEADER) + len(UNRELEASED_HEADER)
        insert = f"\n\n{header}\n\n{line}\n"
        return text[:idx] + insert + text[idx:]

    pattern = re.compile(
        rf"({re.escape(header)}\s*\n)(.*?)(?=\n### |\n## \[|\Z)",
        re.DOTALL,
    )

    def add_line(m: re.Match[str]) -> str:
        body = m.group(2)
        if line.strip() in body:
            return m.group(0)
        addition = line if body.endswith("\n") or not body.strip() else f"\n{line}"
        return m.group(1) + body.rstrip() + addition + "\n"

    return pattern.sub(add_line, text, count=1)


def append_commit_entry(path: Path, commit: CommitInfo) -> bool:
    """Append changelog entry from commit. Returns True if file changed."""
    text = path.read_text(encoding="utf-8")
    section, subject = conventional_changelog_type(commit.subject)
    line = f"- {subject} ({short_sha(commit.sha)})"
    new_text = _insert_under_section(text, section, line)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def append_session_summary(path: Path, summary: str, session_id: str) -> bool:
    text = path.read_text(encoding="utf-8")
    line = f"- Session `{session_id[:8]}`: {summary}"
    new_text = _insert_under_section(text, "Changed", line)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def sync_commits(path: Path, commits: list[CommitInfo]) -> int:
    """Add any missing commit entries. Returns count added."""
    text = path.read_text(encoding="utf-8")
    added = 0
    for commit in commits:
        marker = short_sha(commit.sha)
        if marker in text:
            continue
        section, subject = conventional_changelog_type(commit.subject)
        line = f"- {subject} ({marker})"
        text = _insert_under_section(text, section, line)
        added += 1
    if added:
        path.write_text(text, encoding="utf-8")
    return added
