"""Map file paths to architecture components."""

from __future__ import annotations

from fnmatch import fnmatch

from docubot.config import ComponentRule, Config


def _path_matches(file_path: str, pattern: str) -> bool:
    normalized = file_path.replace("\\", "/")
    p = pattern.replace("\\", "/")
    if fnmatch(normalized, p):
        return True
    if fnmatch(normalized, f"**/{p}"):
        return True
    if p.endswith("/**"):
        prefix = p[:-3]
        if normalized.startswith(prefix + "/") or normalized == prefix:
            return True
    return False


def components_for_files(config: Config, files: list[str]) -> list[str]:
    found: list[str] = []
    rules: list[ComponentRule] = config.components
    for fp in files:
        for rule in rules:
            if any(_path_matches(fp, pat) for pat in rule.paths):
                if rule.name not in found:
                    found.append(rule.name)
    return found
