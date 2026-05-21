from pathlib import Path

from docubot.metadata.schema import load_project_yaml_dict, validate_project_schema


def test_load_project_yaml_dict_rejects_list(tmp_path: Path):
    path = tmp_path / "project.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    assert load_project_yaml_dict(path) is None


def test_validate_project_schema_warns_on_bad_type(tmp_path: Path):
    schema_dir = tmp_path / ".docubot" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "project-metadata.schema.json").write_text(
        '{"type": "object", "properties": {"license": {"type": "string"}}}',
        encoding="utf-8",
    )
    project = tmp_path / ".docubot" / "metadata" / "project.yaml"
    project.parent.mkdir(parents=True)
    project.write_text("license: 42\n", encoding="utf-8")

    report = validate_project_schema(project, tmp_path, strict=False)
    assert report.warnings
    assert any("license" in w for w in report.warnings)
