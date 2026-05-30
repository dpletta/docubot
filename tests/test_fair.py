from pathlib import Path

from docubot.config import Config
from docubot.metadata.fair import compute_fair_score, sync_fair_checklist
from docubot.metadata.project import DataAccess, DataMetadata, ProjectMetadata, Repository
from docubot.state import Manifest


def test_fair_score_with_pid(tmp_path: Path):
    meta = ProjectMetadata(project_title="t", license="MIT", data=DataMetadata())
    meta.data.repository = Repository(
        url="https://example.org/repo",
        persistent_id="10.5281/zenodo.1234567",
    )
    meta.data.standards = ["CSV"]
    (tmp_path / "metadata").mkdir()
    (tmp_path / "metadata" / "datacite.json").write_text("{}", encoding="utf-8")
    config = Config()
    manifest = Manifest(last_sync_commit="abc1234")
    score = compute_fair_score(meta, config, manifest, tmp_path)
    assert score.findable >= 2
    assert score.reusable >= 1


def test_fair_accessible_score_matches_checkbox(tmp_path: Path):
    """Score for 'restrictions/privacy documented' must match the rendered checkbox."""
    meta = ProjectMetadata(project_title="t", license="MIT", data=DataMetadata())
    meta.data.access = DataAccess(controlled_access=False)
    config = Config()
    manifest = Manifest()
    score = compute_fair_score(meta, config, manifest, tmp_path)
    # Only the license point should be awarded; the historical bug also gave
    # a point for `not controlled_access`, contradicting the rendered checklist.
    assert score.accessible == 1

    path = tmp_path / "FAIR.md"
    sync_fair_checklist(path, meta, config, manifest, tmp_path)
    rendered = path.read_text(encoding="utf-8")
    assert "[ ] Access restrictions and privacy considerations documented" in rendered
