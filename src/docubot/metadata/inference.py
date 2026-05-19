"""Infer data modalities and tooling from repository files."""

from __future__ import annotations

from pathlib import Path

MODALITY_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("notebook", (".ipynb",)),
    ("tabular", (".csv", ".tsv", ".parquet", ".xlsx")),
    ("imaging", (".dcm", ".nii", ".nii.gz", ".tif", ".tiff")),
    ("genomic", (".vcf", ".bam", ".fastq", ".fasta", ".bed")),
    ("json_structured", (".json", ".jsonl")),
    ("text", (".txt", ".md")),
]


def infer_modalities(files: list[str]) -> list[str]:
    found: set[str] = set()
    for fp in files:
        lower = fp.lower()
        for name, suffixes in MODALITY_PATTERNS:
            if any(lower.endswith(s) for s in suffixes):
                found.add(name)
        if lower.startswith("data/") or "/data/" in lower:
            found.add("data_directory")
        if lower.startswith("notebooks/") or "/notebooks/" in lower:
            found.add("notebook")
    return sorted(found)


def detect_package_name(repo_root: Path) -> str | None:
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("name"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"').strip("'")
    req = repo_root / "requirements.txt"
    if req.is_file():
        return "requirements.txt dependencies"
    return None


def _sanitize_git_url(url: str) -> str:
    """Remove credentials from git remote URLs before writing to docs."""
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    return f"{scheme}://{rest}"


def git_remote_url(repo_root: Path) -> str | None:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw = out.stdout.strip()
        return _sanitize_git_url(raw) if raw else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
