from pathlib import Path

from docubot.changelog import append_commit_entry
from docubot.git_util import CommitInfo, conventional_changelog_type


def test_conventional_feat():
    section, subject = conventional_changelog_type("feat: add hooks")
    assert section == "Added"
    assert subject == "add hooks"


def test_append_commit_entry(tmp_path: Path):
    chg = tmp_path / "CHANGELOG.md"
    chg.write_text("# Changelog\n\n## [Unreleased]\n\n### Added\n\n", encoding="utf-8")
    commit = CommitInfo(sha="a" * 40, short="aaaaaaa", subject="fix: bug", body="fix: bug\n")
    assert append_commit_entry(chg, commit)
    text = chg.read_text(encoding="utf-8")
    assert "bug" in text
    assert "aaaaaaa" in text
    assert "### Fixed" in text
