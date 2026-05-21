"""Orchestrate FAIR + NIH compliance artifact sync."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from string import Template

from docubot.config import Config
from docubot.metadata.citation import emit_citation_cff
from docubot.metadata.datacite import emit_datacite_json
from docubot.metadata.fair import FairScore, sync_fair_checklist
from docubot.metadata.nih_dms import scaffold_dms_from_template, sync_dms_plan
from docubot.metadata.project import load_project_metadata
from docubot.metadata.validate import validate_compliance
from docubot.paths import templates_dir
from docubot.readme import update_compliance_summary
from docubot.state import ComplianceState, Manifest


def _read_template(repo_root: Path, name: str) -> str | None:
    path = templates_dir(repo_root) / name
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def scaffold_compliance_files(repo_root: Path, config: Config, project_name: str) -> list[str]:
    created: list[str] = []
    meta_path = config.project_metadata_path(repo_root)
    if not meta_path.is_file():
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        tpl = _read_template(repo_root, "project.yaml.tpl")
        if tpl:
            meta_path.write_text(
                Template(tpl).safe_substitute(project_name=project_name),
                encoding="utf-8",
            )
        else:
            meta_path.write_text(f"project:\n  title: {project_name}\n", encoding="utf-8")
        created.append(str(meta_path.relative_to(repo_root)))

    dms_path = config.dms_plan_path(repo_root)
    if not dms_path.is_file():
        tpl = _read_template(repo_root, "DMS_PLAN.md.tpl")
        if tpl:
            scaffold_dms_from_template(dms_path, tpl)
            created.append(str(dms_path.relative_to(repo_root)))

    fair_path = config.fair_checklist_path(repo_root)
    if not fair_path.is_file():
        tpl = _read_template(repo_root, "FAIR_CHECKLIST.md.tpl")
        if tpl:
            fair_path.parent.mkdir(parents=True, exist_ok=True)
            fair_path.write_text(tpl, encoding="utf-8")
            created.append(str(fair_path.relative_to(repo_root)))

    cff_path = config.citation_cff_path(repo_root)
    if not cff_path.is_file():
        tpl = _read_template(repo_root, "CITATION.cff.tpl")
        if tpl:
            cff_path.write_text(
                Template(tpl).safe_substitute(project_name=project_name),
                encoding="utf-8",
            )
            created.append(str(cff_path.relative_to(repo_root)))

    return created


def sync_compliance_artifacts(
    repo_root: Path,
    config: Config,
    manifest: Manifest,
    files: list[str],
) -> tuple[Manifest, list[str]]:
    """Sync DMS, FAIR, DataCite, README compliance block. Returns warnings."""
    meta = load_project_metadata(
        config.project_metadata_path(repo_root),
        project_name=repo_root.name,
    )
    warnings: list[str] = []
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if config.compliance.nih_dms:
        sync_dms_plan(
            config.dms_plan_path(repo_root),
            repo_root,
            meta,
            manifest,
            files,
        )
        if manifest.compliance is None:
            manifest.compliance = ComplianceState()
        manifest.compliance.nih_dms_last_synced = now

    fair_score: FairScore | None = None
    if config.compliance.fair:
        fair_score = sync_fair_checklist(
            config.fair_checklist_path(repo_root),
            meta,
            config,
            manifest,
            repo_root,
        )
        emit_datacite_json(
            config.datacite_path(repo_root),
            meta,
            manifest,
            repo_root,
        )
        if manifest.compliance is None:
            manifest.compliance = ComplianceState()
        manifest.compliance.fair_last_assessed = now
        if fair_score:
            manifest.compliance.fair_score = fair_score.to_dict()

    cff_path = config.citation_cff_path(repo_root)
    if cff_path.is_file() or config.project_metadata_path(repo_root).is_file():
        emit_citation_cff(cff_path, meta, repo_root)
        if manifest.compliance is None:
            manifest.compliance = ComplianceState()
        manifest.compliance.citation_cff_last_synced = now

    report = validate_compliance(meta, config, manifest, repo_root, mode="all")
    warnings = report.warnings + report.errors
    if manifest.compliance is None:
        manifest.compliance = ComplianceState()
    manifest.compliance.validation_warnings = warnings

    update_compliance_summary(
        config.readme_path(repo_root),
        meta,
        config,
        manifest,
        fair_score,
        report,
    )
    return manifest, warnings


def compliance_context_warnings(
    repo_root: Path,
    config: Config,
    manifest: Manifest,
) -> list[str]:
    meta = load_project_metadata(
        config.project_metadata_path(repo_root),
        project_name=repo_root.name,
    )
    report = validate_compliance(meta, config, manifest, repo_root, mode="all")
    return report.warnings[:5]
