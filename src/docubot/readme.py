"""README.md managed block updates."""

from __future__ import annotations

from pathlib import Path
from string import Template

from docubot.blocks import replace_block
from docubot.config import Config
from docubot.metadata.fair import FairScore
from docubot.metadata.project import ProjectMetadata
from docubot.metadata.validate import ComplianceReport
from docubot.state import Manifest, SessionRecord


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


def update_compliance_summary(
    path: Path,
    meta: ProjectMetadata,
    config: Config,
    manifest: Manifest,
    fair_score: FairScore | None,
    report: ComplianceReport,
) -> None:
    if not path.is_file():
        return
    nih_status = "enabled" if config.compliance.nih_dms else "off"
    fair_status = "enabled" if config.compliance.fair else "off"
    score_line = ""
    if fair_score:
        score_line = (
            f"\n| FAIR score (checked) | F:{fair_score.findable}/3 A:{fair_score.accessible}/3 "
            f"I:{fair_score.interoperable}/2 R:{fair_score.reusable}/3 |"
        )
    warn_lines = ""
    if report.warnings:
        warn_lines = "\n\n**Warnings:**\n" + "\n".join(f"- {w}" for w in report.warnings[:8])
    if report.errors:
        warn_lines += "\n\n**Errors:**\n" + "\n".join(f"- {e}" for e in report.errors[:8])

    comp = manifest.compliance
    last_fair = comp.fair_last_assessed if comp else "never"
    last_nih = comp.nih_dms_last_synced if comp else "never"
    dc_path = config.metadata.datacite_output

    content = (
        f"| Check | Status |\n|-------|--------|\n"
        f"| NIH DMS plan | [{config.docs.dms_plan}]({config.docs.dms_plan}) ({nih_status}) |\n"
        f"| FAIR checklist | [{config.docs.fair_checklist}]({config.docs.fair_checklist}) "
        f"({fair_status}) |\n"
        f"| DataCite JSON | [{dc_path}]({dc_path}) |\n"
        f"| Project metadata | `{config.metadata.project_file}` |\n"
        f"| Last FAIR assess | {last_fair} |\n"
        f"| Last DMS sync | {last_nih} |"
        f"{score_line}"
        f"{warn_lines}"
    )
    text = path.read_text(encoding="utf-8")
    path.write_text(replace_block(text, "compliance", content), encoding="utf-8")
