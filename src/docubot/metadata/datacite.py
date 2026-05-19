"""Emit DataCite-compatible JSON metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from docubot.metadata.project import ProjectMetadata
from docubot.state import Manifest


def build_datacite(
    meta: ProjectMetadata,
    manifest: Manifest,
    repo_root: Path,
) -> dict[str, Any]:
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    creators = []
    for c in meta.creators:
        entry: dict[str, Any] = {"name": c.name or "Unknown"}
        if c.orcid:
            entry["nameIdentifiers"] = [
                {
                    "nameIdentifier": c.orcid,
                    "nameIdentifierScheme": "ORCID",
                    "schemeUri": "https://orcid.org",
                }
            ]
        if c.affiliation:
            entry["affiliation"] = [{"name": c.affiliation}]
        creators.append(entry)
    if not creators:
        creators = [{"name": "Unspecified"}]

    titles = [{"title": meta.project_title or repo_root.name}]
    if meta.project_description:
        titles[0]["lang"] = "en"

    rights = []
    lic = meta.data.access.license or meta.license
    if lic:
        rights.append({"rights": lic, "rightsUri": ""})

    funding_refs = []
    for f in meta.funding:
        if f.agency or f.grant_id:
            funding_refs.append(
                {
                    "funderName": f.agency,
                    "awardNumber": f.grant_id,
                }
            )

    repo = meta.data.repository
    identifiers = []
    if repo.persistent_id:
        identifiers.append(
            {
                "identifier": repo.persistent_id,
                "identifierType": "DOI" if repo.persistent_id.startswith("10.") else "URL",
            }
        )

    payload: dict[str, Any] = {
        "schemaVersion": "http://datacite.org/schema/kernel-4",
        "identifier": repo.persistent_id or "",
        "identifiers": identifiers,
        "creators": creators,
        "titles": titles,
        "publisher": repo.name or meta.project_title or repo_root.name,
        "publicationYear": now[:4],
        "dates": [{"date": now, "dateType": "Updated"}],
        "types": {"resourceTypeGeneral": "Software", "resourceType": "Documentation agent"},
        "descriptions": [],
        "rightsList": rights,
        "fundingReferences": funding_refs,
        "version": meta.project_version,
    }
    if meta.project_description:
        payload["descriptions"] = [
            {
                "description": meta.project_description,
                "descriptionType": "Abstract",
            }
        ]
    if repo.url:
        payload["relatedIdentifiers"] = [
            {
                "relatedIdentifier": repo.url,
                "relatedIdentifierType": "URL",
                "relationType": "IsMetadataFor",
            }
        ]
    if manifest.last_sync_commit:
        payload["version"] = f"{meta.project_version}+{manifest.last_sync_commit[:7]}"

    return payload


def emit_datacite_json(
    path: Path,
    meta: ProjectMetadata,
    manifest: Manifest,
    repo_root: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_datacite(meta, manifest, repo_root)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
