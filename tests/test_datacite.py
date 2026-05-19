from pathlib import Path

from docubot.metadata.datacite import build_datacite, emit_datacite_json
from docubot.metadata.project import Creator, Funding, ProjectMetadata, Repository
from docubot.state import Manifest


def test_datacite_required_fields(tmp_path: Path):
    meta = ProjectMetadata(
        project_title="Study",
        project_description="Desc",
        license="CC-BY-4.0",
        creators=[Creator(name="Jane Doe", orcid="https://orcid.org/0000-0002-1825-0097")],
        funding=[Funding(agency="NIH", grant_id="R01GM000001")],
    )
    meta.data.repository = Repository(
        url="https://example.org",
        persistent_id="10.5281/zenodo.1",
    )
    payload = build_datacite(meta, Manifest(last_sync_commit="a" * 40), tmp_path)
    assert payload["titles"][0]["title"] == "Study"
    assert payload["creators"][0]["name"] == "Jane Doe"
    assert payload["fundingReferences"][0]["awardNumber"] == "R01GM000001"


def test_emit_datacite_json(tmp_path: Path):
    out = tmp_path / "metadata" / "datacite.json"
    meta = ProjectMetadata(project_title="t", license="MIT")
    emit_datacite_json(out, meta, Manifest(), tmp_path)
    assert out.is_file()
    assert "schemaVersion" in out.read_text(encoding="utf-8")
