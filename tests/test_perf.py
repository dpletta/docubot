import subprocess
from pathlib import Path

from docubot.config import ComplianceConfig, Config
from docubot.git_util import commits_since
from docubot.metadata.compliance import sync_compliance_artifacts
from docubot.perf import compliance_sync_needed, path_triggers_compliance
from docubot.state import ComplianceState, Manifest


def test_path_triggers_compliance():
    assert path_triggers_compliance(".docubot/metadata/project.yaml")
    assert path_triggers_compliance("notebooks/analysis.ipynb")
    assert not path_triggers_compliance("src/docubot/cli.py")


def test_compliance_sync_needed_when_metadata_changes(tmp_path: Path):
    meta = tmp_path / ".docubot" / "metadata" / "project.yaml"
    meta.parent.mkdir(parents=True)
    meta.write_text("project:\n  title: x\n", encoding="utf-8")
    config = Config(compliance=ComplianceConfig(fair=True, nih_dms=True))
    manifest = Manifest(compliance=ComplianceState(project_metadata_signature="stat:0:0"))
    assert compliance_sync_needed(tmp_path, config, manifest, [])


def test_compliance_sync_skipped_for_unrelated_files(tmp_path: Path):
    meta = tmp_path / ".docubot" / "metadata" / "project.yaml"
    meta.parent.mkdir(parents=True)
    meta.write_text("project:\n  title: x\n", encoding="utf-8")
    dms = tmp_path / "docs" / "DATA_MANAGEMENT_AND_SHARING.md"
    dms.parent.mkdir(parents=True)
    dms.write_text("# DMS\n", encoding="utf-8")
    fair = tmp_path / "docs" / "FAIR_CHECKLIST.md"
    fair.write_text("# FAIR\n", encoding="utf-8")

    from docubot.fingerprint import file_stat_signature

    sig = file_stat_signature(meta)
    config = Config(compliance=ComplianceConfig(fair=True, nih_dms=True))
    manifest = Manifest(
        compliance=ComplianceState(
            project_metadata_signature=sig,
            nih_dms_last_synced="2026-01-01T00:00:00Z",
            fair_last_assessed="2026-01-01T00:00:00Z",
            validation_warnings=["cached warning"],
        )
    )
    assert not compliance_sync_needed(tmp_path, config, manifest, ["src/foo.py"])


def test_sync_compliance_artifacts_skips_when_unchanged(tmp_path: Path):
    meta = tmp_path / ".docubot" / "metadata" / "project.yaml"
    meta.parent.mkdir(parents=True)
    meta.write_text("project:\n  title: x\nlicense: MIT\n", encoding="utf-8")
    dms = tmp_path / "docs" / "DATA_MANAGEMENT_AND_SHARING.md"
    dms.parent.mkdir(parents=True)
    dms.write_text("# DMS\n", encoding="utf-8")
    fair = tmp_path / "docs" / "FAIR_CHECKLIST.md"
    fair.write_text("# FAIR\n", encoding="utf-8")

    from docubot.fingerprint import file_stat_signature

    sig = file_stat_signature(meta)
    config = Config(compliance=ComplianceConfig(fair=True, nih_dms=True))
    manifest = Manifest(
        compliance=ComplianceState(
            project_metadata_signature=sig,
            nih_dms_last_synced="2026-01-01T00:00:00Z",
            fair_last_assessed="2026-01-01T00:00:00Z",
            validation_warnings=["cached"],
        )
    )
    before = dms.read_text(encoding="utf-8")
    manifest, warnings = sync_compliance_artifacts(
        tmp_path, config, manifest, ["src/only.py"]
    )
    assert dms.read_text(encoding="utf-8") == before
    assert warnings == ["cached"]


def test_commits_since_single_git_invocation(tmp_path: Path, monkeypatch):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "a.txt").write_text("1\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: one"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    (repo / "b.txt").write_text("2\n", encoding="utf-8")
    subprocess.run(["git", "add", "b.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fix: two"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    calls: list[list[str]] = []
    real_run = subprocess.run

    def spy(cmd, *args, **kwargs):
        if cmd and cmd[0] == "git":
            calls.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr("docubot.git_util.subprocess.run", spy)
    result = commits_since(repo, base)
    assert len(result) == 1
    log_calls = [c for c in calls if "log" in c]
    assert len(log_calls) == 1
