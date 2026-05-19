"""FAIR checklist generation and scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from docubot.blocks import replace_block
from docubot.config import Config
from docubot.metadata.project import ProjectMetadata
from docubot.state import Manifest


@dataclass
class FairScore:
    findable: int = 0
    accessible: int = 0
    interoperable: int = 0
    reusable: int = 0

    def total(self) -> int:
        return self.findable + self.accessible + self.interoperable + self.reusable

    def to_dict(self) -> dict[str, int]:
        return {
            "findable": self.findable,
            "accessible": self.accessible,
            "interoperable": self.interoperable,
            "reusable": self.reusable,
        }


def ensure_fair_checklist(path: Path, template_text: str | None = None) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        template_text
        or "# FAIR Checklist\n\n_Assess Findable, Accessible, Interoperable, Reusable._\n",
        encoding="utf-8",
    )


def compute_fair_score(
    meta: ProjectMetadata,
    config: Config,
    manifest: Manifest,
    repo_root: Path,
) -> FairScore:
    score = FairScore()
    repo = meta.data.repository
    acc = meta.data.access

    # Findable (max 3)
    if repo.url:
        score.findable += 1
    if repo.persistent_id:
        score.findable += 1
    if (repo_root / config.metadata.datacite_output).is_file():
        score.findable += 1

    # Accessible (max 3)
    if acc.license or meta.license:
        score.accessible += 1
    if acc.restrictions or acc.privacy_notes or not acc.controlled_access:
        score.accessible += 1
    if repo.share_timeline:
        score.accessible += 1

    # Interoperable (max 2)
    if meta.data.standards:
        score.interoperable += 1
    if (repo_root / config.docs.architecture).is_file():
        score.interoperable += 1

    # Reusable (max 3)
    if meta.license:
        score.reusable += 1
    if manifest.last_sync_commit:
        score.reusable += 1
    if meta.data.types_narrative or meta.data.preserved_and_shared:
        score.reusable += 1

    return score


def _checkbox(ok: bool, label: str) -> str:
    return f"- [{'x' if ok else ' '}] {label}"


def sync_fair_checklist(
    path: Path,
    meta: ProjectMetadata,
    config: Config,
    manifest: Manifest,
    repo_root: Path,
) -> FairScore:
    ensure_fair_checklist(path)
    score = compute_fair_score(meta, config, manifest, repo_root)
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    repo = meta.data.repository
    acc = meta.data.access

    findable = "\n".join(
        [
            _checkbox(bool(repo.url), "Repository URL is documented"),
            _checkbox(bool(repo.persistent_id), "Persistent identifier (DOI/PID) is assigned"),
            _checkbox(
                (repo_root / config.metadata.datacite_output).is_file(),
                "Machine-readable metadata file exists (metadata/datacite.json)",
            ),
        ]
    )
    accessible = "\n".join(
        [
            _checkbox(bool(acc.license or meta.license), "Usage license is specified (SPDX)"),
            _checkbox(
                bool(acc.restrictions or acc.privacy_notes or acc.consent_notes),
                "Access restrictions and privacy considerations documented",
            ),
            _checkbox(bool(repo.share_timeline), "Access timeline documented"),
        ]
    )
    interoperable = "\n".join(
        [
            _checkbox(bool(meta.data.standards), "Data standards/formats listed"),
            _checkbox(
                (repo_root / config.docs.architecture).is_file(),
                "Architecture / data flow documentation present",
            ),
        ]
    )
    reusable = "\n".join(
        [
            _checkbox(bool(meta.license), "Project license declared"),
            _checkbox(bool(manifest.last_sync_commit), "Provenance tracked via git sync commit"),
            _checkbox(
                bool(meta.data.types_narrative or meta.data.preserved_and_shared),
                "Data description supports fitness-for-purpose",
            ),
        ]
    )

    summary = (
        f"Last assessed: **{ts}**  \n"
        f"Scores (checked items): Findable {score.findable}/3, "
        f"Accessible {score.accessible}/3, "
        f"Interoperable {score.interoperable}/2, "
        f"Reusable {score.reusable}/3"
    )

    text = path.read_text(encoding="utf-8")
    text = replace_block(text, "fair-summary", summary)
    text = replace_block(text, "fair-findable", findable)
    text = replace_block(text, "fair-accessible", accessible)
    text = replace_block(text, "fair-interoperable", interoperable)
    text = replace_block(text, "fair-reusable", reusable)
    path.write_text(text, encoding="utf-8")
    return score
