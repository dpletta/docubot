import subprocess
from pathlib import Path


def test_session_finalize_idempotent(tmp_path: Path, monkeypatch):
    """End-to-end session start + finalize in a temp git repo."""
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Copy minimal docubot config
    (repo / ".docubot").mkdir()
    (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Added\n\n", encoding="utf-8"
    )
    (repo / "docs").mkdir()
    arch = (
        "# Architecture\n\n<!-- docubot:session-activity -->\n"
        "_none_\n<!-- /docubot:session-activity -->\n"
    )
    (repo / "docs" / "ARCHITECTURE.md").write_text(arch, encoding="utf-8")
    (repo / "README.md").write_text(
        "# Test\n\n<!-- docubot:recent-sessions -->\n_none_\n<!-- /docubot:recent-sessions -->\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    monkeypatch.chdir(repo)
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))

    from docubot.session import session_finalize, session_start
    from docubot.state import load_manifest

    r1 = session_start({"conversation_id": "c1", "generation_id": "g1"})
    assert "session_id" in r1

    from docubot.session import session_track

    session_track("src/app.py")

    fin = session_finalize(
        reason="test",
        conversation_id="c1",
        generation_id="g1",
    )
    assert fin["status"] == "ok"

    fin2 = session_finalize(
        reason="test",
        conversation_id="c1",
        generation_id="g1",
    )
    assert fin2["status"] == "skipped"

    manifest = load_manifest(repo)
    assert len(manifest.sessions) == 1
    readme = (repo / "README.md").read_text(encoding="utf-8")
    assert "docubot:recent-sessions" in readme
