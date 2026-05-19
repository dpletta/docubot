from pathlib import Path

from docubot.config import Config
from docubot.metadata.fair import compute_fair_score
from docubot.metadata.project import DataMetadata, ProjectMetadata, Repository
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
