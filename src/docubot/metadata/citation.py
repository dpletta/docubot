"""Sync CITATION.cff from project metadata (CFF 1.2.0)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from docubot.metadata.inference import git_remote_url
from docubot.metadata.project import Creator, ProjectMetadata


def _split_name(full: str) -> tuple[str, str]:
    parts = full.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return "", parts[0]
    return " ".join(parts[:-1]), parts[-1]


def _orcid_url(orcid: str) -> str:
    o = orcid.strip()
    if not o:
        return ""
    if o.startswith("http"):
        return o
    if o.startswith("0000-"):
        return f"https://orcid.org/{o}"
    return o


def _author_entry(creator: Creator) -> dict[str, str]:
    given, family = _split_name(creator.name)
    entry: dict[str, str] = {}
    if family:
        entry["family-names"] = family
    if given:
        entry["given-names"] = given
    if not entry:
        entry["family-names"] = creator.name or "Unknown"
    orcid = _orcid_url(creator.orcid)
    if orcid:
        entry["orcid"] = orcid
    return entry


def build_citation_cff(meta: ProjectMetadata, repo_root: Path) -> dict[str, Any]:
    """Build a CFF 1.2.0 document from project metadata."""
    authors = [_author_entry(c) for c in meta.creators]
    if not authors:
        authors = [{"family-names": "Unspecified"}]

    repo_url = meta.data.repository.url.strip() or git_remote_url(repo_root) or ""
    lic = meta.license or meta.data.access.license or ""

    payload: dict[str, Any] = {
        "cff-version": "1.2.0",
        "message": "If you use this software, please cite it as below.",
        "title": meta.project_title or repo_root.name,
        "version": meta.project_version,
        "authors": authors,
    }
    if lic:
        payload["license"] = lic
    if repo_url:
        payload["repository-code"] = repo_url
    pid = meta.data.repository.persistent_id.strip()
    if pid:
        if pid.startswith("10."):
            payload["doi"] = pid
        else:
            payload["identifiers"] = [
                {
                    "type": "other",
                    "value": pid,
                    "description": "Persistent identifier",
                }
            ]
    keywords = sorted({t for t in meta.data.types if t})
    if keywords:
        payload["keywords"] = keywords
    if meta.project_description:
        payload["abstract"] = meta.project_description.strip()
    return payload


def emit_citation_cff(path: Path, meta: ProjectMetadata, repo_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_citation_cff(meta, repo_root)
    path.write_text(
        yaml.dump(payload, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
