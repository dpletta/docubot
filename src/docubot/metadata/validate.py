"""Compliance validation for FAIR and NIH DMS metadata."""

from __future__ import annotations

from dataclasses import dataclass, field

from docubot.config import Config
from docubot.metadata.fair import compute_fair_score
from docubot.metadata.project import ProjectMetadata
from docubot.state import Manifest


@dataclass
class ComplianceReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_nih(meta: ProjectMetadata, strict: bool) -> ComplianceReport:
    report = ComplianceReport()
    for f in meta.funding:
        if f.agency.upper() == "NIH" and not f.grant_id.strip():
            msg = "NIH funding listed but grant_id is empty (NOT-OD-21-014 oversight)"
            if strict:
                report.add_error(msg)
            else:
                report.add_warning(msg)
    if not meta.oversight.responsible_party.strip():
        msg = "oversight.responsible_party is not set (DMS Element 6)"
        if strict:
            report.add_error(msg)
        else:
            report.add_warning(msg)
    if not meta.data.repository.url.strip():
        report.add_warning("data.repository.url is not set (DMS Element 4 / FAIR Findable)")
    if not meta.data.repository.persistent_id.strip():
        report.add_warning("data.repository.persistent_id is not set (FAIR Findable)")
    if not meta.data.types_narrative.strip() and not meta.data.types:
        report.add_warning("No data types described (DMS Element 1)")
    return report


def validate_fair(
    meta: ProjectMetadata,
    config: Config,
    manifest: Manifest,
    repo_root,
    strict: bool,
) -> ComplianceReport:
    report = ComplianceReport()
    score = compute_fair_score(meta, config, manifest, repo_root)
    if score.findable < 2:
        msg = f"FAIR Findable score low ({score.findable}/3): set repository URL and PID"
        if strict:
            report.add_error(msg)
        else:
            report.add_warning(msg)
    if not (meta.license or meta.data.access.license):
        msg = "No license specified (FAIR Accessible/Reusable)"
        if strict:
            report.add_error(msg)
        else:
            report.add_warning(msg)
    return report


def validate_compliance(
    meta: ProjectMetadata,
    config: Config,
    manifest: Manifest,
    repo_root,
    *,
    mode: str = "all",
) -> ComplianceReport:
    strict = config.compliance.strict
    combined = ComplianceReport()
    if mode in ("all", "nih") and config.compliance.nih_dms:
        nih = validate_nih(meta, strict)
        combined.errors.extend(nih.errors)
        combined.warnings.extend(nih.warnings)
        combined.ok = combined.ok and nih.ok
    if mode in ("all", "fair") and config.compliance.fair:
        fair = validate_fair(meta, config, manifest, repo_root, strict)
        combined.errors.extend(fair.errors)
        combined.warnings.extend(fair.warnings)
        combined.ok = combined.ok and fair.ok
    return combined
