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
    # Disable commit signing so the test is independent of the developer's
    # global git config (some CI/cloud environments enforce signing globally).
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
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


def test_session_start_scaffolds_compliance_when_manifest_missing(
    tmp_path: Path, monkeypatch
):
    repo = tmp_path / "proj"
    repo.mkdir()
    monkeypatch.chdir(repo)

    from types import SimpleNamespace

    from docubot.state import Manifest, save_manifest

    compliance_calls: list[str] = []

    def fake_scaffold_docs(root: Path, project_name: str) -> list[str]:
        save_manifest(root, Manifest())
        return [".docubot/manifest.json"]

    def fake_scaffold_compliance_files(root: Path, config, project_name: str) -> list[str]:
        compliance_calls.append(project_name)
        return []

    monkeypatch.setattr("docubot.session.scaffold_docs", fake_scaffold_docs)
    monkeypatch.setattr(
        "docubot.session.scaffold_compliance_files",
        fake_scaffold_compliance_files,
    )
    monkeypatch.setattr(
        "docubot.session.check_stale",
        lambda *args: SimpleNamespace(stale=False, reason=None, changed_files=[]),
    )
    monkeypatch.setattr("docubot.session.compliance_context_warnings", lambda *args: [])

    from docubot.session import session_start

    result = session_start({"conversation_id": "c1", "generation_id": "g1"})

    assert "session_id" in result
    assert compliance_calls == ["proj"]
