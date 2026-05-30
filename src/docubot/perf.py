"""Performance helpers for hot paths (hooks, sync, staleness)."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from docubot.config import Config
from docubot.fingerprint import file_stat_signature
from docubot.state import Manifest

# Paths that should trigger a full compliance artifact sync when touched.
COMPLIANCE_PATH_PREFIXES = (
    ".docubot/metadata/",
    ".docubot/config",
    "metadata/",
    "data/",
    "notebooks/",
    "CITATION.cff",
    "docs/DATA_MANAGEMENT_AND_SHARING.md",
    "docs/FAIR_CHECKLIST.md",
)


def path_triggers_compliance(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    for prefix in COMPLIANCE_PATH_PREFIXES:
        if normalized.startswith(prefix) or normalized == prefix:
            return True
    for pattern in ("*.vcf", "*.bam", "*.fastq", "*.fasta", "*.bed", "*.ipynb"):
        if fnmatch(normalized, pattern):
            return True
    return False


def compliance_sync_needed(
    repo_root: Path,
    config: Config,
    manifest: Manifest,
    files: list[str],
) -> bool:
    """Return True when FAIR/NIH/CITATION sync should run (expensive path)."""
    if not config.compliance.nih_dms and not config.compliance.fair:
        return False

    meta_path = config.project_metadata_path(repo_root)
    if meta_path.is_file():
        sig = file_stat_signature(meta_path)
        comp = manifest.compliance
        if comp is None or comp.project_metadata_signature != sig:
            return True

    if any(path_triggers_compliance(f) for f in files):
        return True

    if not config.dms_plan_path(repo_root).is_file():
        return True
    if config.compliance.fair and not config.fair_checklist_path(repo_root).is_file():
        return True

    comp = manifest.compliance
    if comp is None:
        return True
    if config.compliance.nih_dms and not comp.nih_dms_last_synced:
        return True
    if config.compliance.fair and not comp.fair_last_assessed:
        return True

    return False


def doc_fingerprint_unchanged(path: Path, manifest: Manifest, rel: str) -> bool:
    """True if path stat matches last recorded signature (skip sha256 re-read)."""
    if not path.is_file():
        return False
    sig = file_stat_signature(path)
    return manifest.doc_stat_signatures.get(rel) == sig and rel in manifest.doc_fingerprints
