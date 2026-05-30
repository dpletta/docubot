"""Validate project.yaml against the bundled JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from docubot.metadata.report import ComplianceReport
from docubot.paths import schema_dir


def load_project_yaml_dict(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        return None
    return loaded


def validate_project_schema(
    project_yaml_path: Path,
    repo_root: Path,
    *,
    strict: bool,
) -> ComplianceReport:
    report = ComplianceReport()
    raw = load_project_yaml_dict(project_yaml_path)
    if raw is None:
        msg = f"{project_yaml_path.name} must be a YAML mapping (object)"
        if strict:
            report.add_error(msg)
        else:
            report.add_warning(msg)
        return report

    schema_path = schema_dir(repo_root) / "project-metadata.schema.json"
    if not schema_path.is_file():
        report.add_warning("project-metadata JSON Schema not found; skipping schema check")
        return report

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(raw), key=lambda e: list(e.path))
    for err in errors:
        loc = ".".join(str(p) for p in err.path) or "(root)"
        msg = f"project.yaml schema: {loc}: {err.message}"
        if strict:
            report.add_error(msg)
        else:
            report.add_warning(msg)
    return report
