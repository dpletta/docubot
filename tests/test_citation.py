from pathlib import Path

import yaml

from docubot.metadata.citation import build_citation_cff, emit_citation_cff
from docubot.metadata.project import Creator, DataMetadata, ProjectMetadata, Repository


def test_build_citation_cff_maps_creators_and_doi(tmp_path: Path):
    meta = ProjectMetadata(
        project_title="My Study",
        project_version="1.2.0",
        license="MIT",
        creators=[
            Creator(name="Ada Lovelace", orcid="0000-0000-0000-0001"),
        ],
        data=DataMetadata(
            repository=Repository(
                url="https://github.com/example/repo",
                persistent_id="10.5281/zenodo.123",
            ),
        ),
    )
    payload = build_citation_cff(meta, tmp_path)
    assert payload["title"] == "My Study"
    assert payload["doi"] == "10.5281/zenodo.123"
    assert payload["repository-code"] == "https://github.com/example/repo"
    assert payload["authors"][0]["family-names"] == "Lovelace"
    assert payload["authors"][0]["given-names"] == "Ada"
    assert "orcid.org" in payload["authors"][0]["orcid"]


def test_emit_citation_cff_writes_yaml(tmp_path: Path):
    meta = ProjectMetadata(project_title="Emit Test", license="Apache-2.0")
    out = tmp_path / "CITATION.cff"
    emit_citation_cff(out, meta, tmp_path)
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["cff-version"] == "1.2.0"
    assert loaded["title"] == "Emit Test"
    assert loaded["license"] == "Apache-2.0"
