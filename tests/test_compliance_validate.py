from pathlib import Path

from click.testing import CliRunner

from docubot.cli import main
from docubot.config import ComplianceConfig, Config
from docubot.metadata.project import Funding, ProjectMetadata, load_project_metadata
from docubot.metadata.validate import validate_compliance, validate_nih
from docubot.state import Manifest


def test_validate_nih_strict_grant():
    meta = ProjectMetadata(funding=[Funding(agency="NIH", grant_id="")])
    report = validate_nih(meta, strict=True)
    assert not report.ok
    assert any("grant_id" in e for e in report.errors)


def test_validate_compliance_fair_warning(tmp_path: Path):
    meta = ProjectMetadata(license="MIT")
    config = Config(compliance=ComplianceConfig(fair=True, nih_dms=False, strict=False))
    report = validate_compliance(meta, config, Manifest(), tmp_path, mode="fair")
    assert report.warnings  # no PID


def test_cli_validate_compliance():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--compliance", "all"])
    assert result.exit_code == 0 or "Compliance warning" in result.output


def test_load_project_metadata_ignores_non_mapping_yaml(tmp_path: Path):
    metadata_path = tmp_path / "project.yaml"
    metadata_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    meta = load_project_metadata(metadata_path, "fallback-name")

    assert meta.project_title == "fallback-name"
    assert meta.raw == {}
