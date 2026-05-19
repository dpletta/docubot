"""README.md managed block updates."""

from __future__ import annotations

from pathlib import Path
from string import Template

from docubot.blocks import replace_block
from docubot.state import SessionRecord


def ensure_readme(
    path: Path,
    template_text: str | None = None,
    project_name: str = "Project",
) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if template_text:
        text = Template(template_text).safe_substitute(project_name=project_name)
    else:
        text = f"# {project_name}\n\n<!-- docubot:overview -->\n\n<!-- /docubot:overview -->\n"
    path.write_text(text, encoding="utf-8")


def format_session_entry(record: SessionRecord) -> str:
    end = record.ended_at or "in progress"
    files = len(record.files_touched)
    commits = len(record.commits)
    comps = ", ".join(record.components_touched) if record.components_touched else "none"
    summary = f" — {record.summary}" if record.summary else ""
    return (
        f"- **{record.started_at[:10]}** `{record.id[:8]}` "
        f"({record.branch or 'unknown'}): {files} files, {commits} commits, "
        f"components: {comps}. Ended: {end}{summary}"
    )


def update_recent_sessions(path: Path, sessions: list[SessionRecord], limit: int = 10) -> None:
    text = path.read_text(encoding="utf-8")
    ended = [s for s in sessions if s.ended_at]
    ended.sort(key=lambda s: s.ended_at or "", reverse=True)
    if not ended:
        content = "_No sessions finalized yet._"
    else:
        content = "\n".join(format_session_entry(s) for s in ended[:limit])
    new_text = replace_block(text, "recent-sessions", content)
    path.write_text(new_text, encoding="utf-8")
