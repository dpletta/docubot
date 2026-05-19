"""docs/ARCHITECTURE.md maintenance."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from docubot.blocks import replace_block
from docubot.components import components_for_files
from docubot.config import Config


def ensure_architecture(path: Path, template_text: str | None = None) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        template_text or "# Architecture\n\n## Session Activity\n\n_No sessions yet._\n",
        encoding="utf-8",
    )


def append_session_activity(
    path: Path,
    *,
    session_id: str,
    branch: str | None,
    files: list[str],
    components: list[str],
    commit_count: int,
    summary: str | None = None,
) -> None:
    text = path.read_text(encoding="utf-8")
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    comp = ", ".join(components) if components else "none"
    file_count = len(files)
    line = (
        f"- **{ts}** — session `{session_id[:8]}` on branch `{branch or 'unknown'}`: "
        f"{file_count} file(s), {commit_count} commit(s), components: {comp}."
    )
    if summary:
        line += f" {summary}"

    block_name = "session-activity"
    from docubot.blocks import get_block

    existing = get_block(text, block_name) or "_No sessions recorded yet._"
    if existing.startswith("_No sessions"):
        new_content = line
    else:
        new_content = line + "\n" + existing

    new_text = replace_block(text, block_name, new_content)
    path.write_text(new_text, encoding="utf-8")


def update_components_table(path: Path, config: Config) -> None:
    """Refresh components table from config rules."""
    if not config.components:
        return
    text = path.read_text(encoding="utf-8")
    rows = [
        f"| {r.name} | _auto-tracked_ | `{', '.join(r.paths)}` |" for r in config.components
    ]
    header = "| Component | Responsibility | Paths |\n|-----------|----------------|-------|"
    table = header + "\n" + "\n".join(rows)
    # Replace between ## Components and next ##
    import re

    pattern = re.compile(
        r"(## Components\s*\n)(.*?)(\n## )",
        re.DOTALL,
    )
    if pattern.search(text):
        text = pattern.sub(rf"\1\n{table}\n\3", text, count=1)
        path.write_text(text, encoding="utf-8")


def sync_architecture(
    path: Path,
    config: Config,
    *,
    session_id: str,
    branch: str | None,
    files: list[str],
    commit_count: int,
    summary: str | None = None,
) -> None:
    ensure_architecture(path)
    components = components_for_files(config, files)
    append_session_activity(
        path,
        session_id=session_id,
        branch=branch,
        files=files,
        components=components,
        commit_count=commit_count,
        summary=summary,
    )
    update_components_table(path, config)
