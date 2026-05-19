"""NIH Data Management and Sharing Plan markdown sync."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from docubot.blocks import replace_block
from docubot.metadata.inference import detect_package_name, git_remote_url, infer_modalities
from docubot.metadata.project import ProjectMetadata
from docubot.state import Manifest


def ensure_dms_plan(path: Path, template_text: str | None = None) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        template_text
        or "# Data Management and Sharing Plan\n\n_See NOT-OD-21-014._\n",
        encoding="utf-8",
    )


def _detected_types_block(files: list[str]) -> str:
    modalities = infer_modalities(files)
    if not modalities:
        return "_No data file patterns detected in recent session._"
    return "\n".join(f"- Detected modality: `{m}`" for m in modalities)


def _tools_block(repo_root: Path, meta: ProjectMetadata) -> str:
    lines: list[str] = []
    if meta.data.tools_code:
        lines.append(meta.data.tools_code)
    pkg = detect_package_name(repo_root)
    if pkg:
        lines.append(f"\n- Package/dependencies: `{pkg}`")
    remote = git_remote_url(repo_root)
    if remote:
        lines.append(f"- Source repository: `{remote}`")
    if not lines:
        lines.append("_Describe tools, software, and code required to access or reuse data._")
    return "\n".join(lines)


def _standards_block(meta: ProjectMetadata) -> str:
    if meta.data.standards:
        return "\n".join(f"- {s}" for s in meta.data.standards)
    return "_List applicable data formats, dictionaries, and identifiers._"


def _preservation_block(meta: ProjectMetadata) -> str:
    repo = meta.data.repository
    lines = [
        f"- **Repository:** {repo.name or '_not set_'}",
        f"- **URL:** {repo.url or '_not set_'}",
        f"- **Persistent ID:** {repo.persistent_id or '_not set — required for FAIR Findable_'}",
        f"- **Share timeline:** {repo.share_timeline or '_not set_'}",
        f"- **Retention:** {repo.retention_period or '_not set_'}",
    ]
    return "\n".join(lines)


def _access_block(meta: ProjectMetadata) -> str:
    acc = meta.data.access
    lines = [
        f"- **License:** {acc.license or meta.license or '_not set_'}",
        f"- **Controlled access:** {'yes' if acc.controlled_access else 'no'}",
    ]
    if acc.consent_notes:
        lines.append(f"- **Informed consent:** {acc.consent_notes}")
    if acc.privacy_notes:
        lines.append(f"- **Privacy/confidentiality:** {acc.privacy_notes}")
    if acc.restrictions:
        lines.append(f"- **Restrictions:** {acc.restrictions}")
    if len(lines) == 2 and not acc.restrictions:
        lines.append("_Document consent, privacy, and reuse limitations per NOT-OD-21-014._")
    return "\n".join(lines)


def _oversight_block(meta: ProjectMetadata, manifest: Manifest) -> str:
    lines = [
        f"- **Responsible party:** {meta.oversight.responsible_party or '_not set_'}",
        f"- **Review frequency:** {meta.oversight.review_frequency or '_not set_'}",
    ]
    if manifest.last_sync_at:
        lines.append(f"- **Last docubot sync:** {manifest.last_sync_at}")
    if manifest.sessions:
        last = manifest.sessions[-1]
        lines.append(
            f"- **Last session finalized:** {last.ended_at or last.started_at} "
            f"(`{last.id[:8]}`)"
        )
    return "\n".join(lines)


def sync_dms_plan(
    path: Path,
    repo_root: Path,
    meta: ProjectMetadata,
    manifest: Manifest,
    files: list[str],
) -> None:
    ensure_dms_plan(path)
    text = path.read_text(encoding="utf-8")
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    types_user = meta.data.types_narrative or "_Provide narrative per NOT-OD-21-014 Element 1._"
    types_detected = _detected_types_block(files)
    element1 = (
        f"_Auto-synced {ts}_\n\n"
        f"**Configured types:** {', '.join(meta.data.types) or 'none'}\n\n"
        f"{types_user}\n\n"
        f"**Preserved and shared:**\n{meta.data.preserved_and_shared or '_not described_'}\n\n"
        f"**Not shared rationale:**\n{meta.data.not_shared_rationale or '_not described_'}\n\n"
        f"**Detected in repository:**\n{types_detected}"
    )

    docs_list = meta.data.related_documentation
    if docs_list:
        element1 += "\n\n**Related documentation:**\n" + "\n".join(
            f"- `{d}`" for d in docs_list
        )

    blocks = {
        "dms-data-type": element1,
        "dms-tools-code": _tools_block(repo_root, meta),
        "dms-standards": _standards_block(meta),
        "dms-preservation": _preservation_block(meta),
        "dms-access": _access_block(meta),
        "dms-oversight": _oversight_block(meta, manifest),
    }
    for name, content in blocks.items():
        text = replace_block(text, name, content)
    path.write_text(text, encoding="utf-8")


def scaffold_dms_from_template(path: Path, template_text: str) -> None:
    ensure_dms_plan(path, template_text)
