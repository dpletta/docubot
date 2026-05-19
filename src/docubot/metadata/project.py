"""Load project metadata from .docubot/metadata/project.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Creator:
    name: str = ""
    orcid: str = ""
    affiliation: str = ""
    role: str = ""


@dataclass
class Funding:
    agency: str = ""
    grant_id: str = ""


@dataclass
class Repository:
    name: str = ""
    url: str = ""
    persistent_id: str = ""
    share_timeline: str = ""
    retention_period: str = ""


@dataclass
class DataAccess:
    license: str = ""
    controlled_access: bool = False
    restrictions: str = ""
    consent_notes: str = ""
    privacy_notes: str = ""


@dataclass
class DataMetadata:
    types: list[str] = field(default_factory=list)
    types_narrative: str = ""
    preserved_and_shared: str = ""
    not_shared_rationale: str = ""
    related_documentation: list[str] = field(default_factory=list)
    tools_code: str = ""
    standards: list[str] = field(default_factory=list)
    repository: Repository = field(default_factory=Repository)
    access: DataAccess = field(default_factory=DataAccess)


@dataclass
class Oversight:
    responsible_party: str = ""
    review_frequency: str = ""


@dataclass
class ProjectMetadata:
    project_title: str = ""
    project_description: str = ""
    project_version: str = "0.1.0"
    creators: list[Creator] = field(default_factory=list)
    funding: list[Funding] = field(default_factory=list)
    license: str = ""
    data: DataMetadata = field(default_factory=DataMetadata)
    oversight: Oversight = field(default_factory=Oversight)
    raw: dict[str, Any] = field(default_factory=dict)


def _get_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    val = raw.get(key)
    return val if isinstance(val, dict) else {}


def load_project_metadata(path: Path, project_name: str = "project") -> ProjectMetadata:
    if not path.is_file():
        return ProjectMetadata(project_title=project_name)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw: dict[str, Any] = loaded if isinstance(loaded, dict) else {}
    proj = _get_dict(raw, "project")
    data_raw = _get_dict(raw, "data")
    repo_raw = _get_dict(data_raw, "repository")
    access_raw = _get_dict(data_raw, "access")
    oversight_raw = _get_dict(raw, "oversight")

    creators = [
        Creator(
            name=str(c.get("name", "")),
            orcid=str(c.get("orcid", "")),
            affiliation=str(c.get("affiliation", "")),
            role=str(c.get("role", "")),
        )
        for c in (raw.get("creators") or [])
        if isinstance(c, dict)
    ]
    funding = [
        Funding(agency=str(f.get("agency", "")), grant_id=str(f.get("grant_id", "")))
        for f in (raw.get("funding") or [])
        if isinstance(f, dict)
    ]

    return ProjectMetadata(
        project_title=str(proj.get("title") or project_name),
        project_description=str(proj.get("description") or ""),
        project_version=str(proj.get("version") or "0.1.0"),
        creators=creators,
        funding=funding,
        license=str(raw.get("license") or ""),
        data=DataMetadata(
            types=[str(t) for t in (data_raw.get("types") or [])],
            types_narrative=str(data_raw.get("types_narrative") or "").strip(),
            preserved_and_shared=str(data_raw.get("preserved_and_shared") or "").strip(),
            not_shared_rationale=str(data_raw.get("not_shared_rationale") or "").strip(),
            related_documentation=[
                str(d) for d in (data_raw.get("related_documentation") or [])
            ],
            tools_code=str(data_raw.get("tools_code") or "").strip(),
            standards=[str(s) for s in (data_raw.get("standards") or [])],
            repository=Repository(
                name=str(repo_raw.get("name") or ""),
                url=str(repo_raw.get("url") or ""),
                persistent_id=str(repo_raw.get("persistent_id") or ""),
                share_timeline=str(repo_raw.get("share_timeline") or ""),
                retention_period=str(repo_raw.get("retention_period") or ""),
            ),
            access=DataAccess(
                license=str(access_raw.get("license") or raw.get("license") or ""),
                controlled_access=bool(access_raw.get("controlled_access", False)),
                restrictions=str(access_raw.get("restrictions") or "").strip(),
                consent_notes=str(access_raw.get("consent_notes") or "").strip(),
                privacy_notes=str(access_raw.get("privacy_notes") or "").strip(),
            ),
        ),
        oversight=Oversight(
            responsible_party=str(oversight_raw.get("responsible_party") or ""),
            review_frequency=str(oversight_raw.get("review_frequency") or ""),
        ),
        raw=raw,
    )
