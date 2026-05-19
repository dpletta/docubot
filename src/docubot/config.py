"""Load and validate docubot configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from docubot.paths import config_path


@dataclass
class ComponentRule:
    name: str
    paths: list[str]


@dataclass
class LlmConfig:
    enabled: bool = False
    model: str = "gpt-4o-mini"
    max_tokens: int = 512


@dataclass
class DocsConfig:
    changelog: str = "CHANGELOG.md"
    architecture: str = "docs/ARCHITECTURE.md"
    readme: str = "README.md"


@dataclass
class Config:
    schema_version: int = 1
    watch_paths: list[str] = field(
        default_factory=lambda: ["src/**", "lib/**", "*.py", "*.ipynb"]
    )
    docs: DocsConfig = field(default_factory=DocsConfig)
    components: list[ComponentRule] = field(default_factory=list)
    stale_check: str = "warn"
    llm: LlmConfig = field(default_factory=LlmConfig)
    preserve_sections: bool = True

    def changelog_path(self, repo_root: Path) -> Path:
        return repo_root / self.docs.changelog

    def architecture_path(self, repo_root: Path) -> Path:
        return repo_root / self.docs.architecture

    def readme_path(self, repo_root: Path) -> Path:
        return repo_root / self.docs.readme


def load_config(repo_root: Path) -> Config:
    path = config_path(repo_root)
    if not path.is_file():
        return Config()
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    docs_raw = raw.get("docs") or {}
    llm_raw = raw.get("llm") or {}
    components = [
        ComponentRule(name=c["name"], paths=list(c.get("paths") or []))
        for c in (raw.get("components") or [])
        if isinstance(c, dict) and c.get("name")
    ]
    return Config(
        schema_version=int(raw.get("schema_version", 1)),
        watch_paths=list(raw.get("watch_paths") or Config().watch_paths),
        docs=DocsConfig(
            changelog=str(docs_raw.get("changelog", "CHANGELOG.md")),
            architecture=str(docs_raw.get("architecture", "docs/ARCHITECTURE.md")),
            readme=str(docs_raw.get("readme", "README.md")),
        ),
        components=components,
        stale_check=str(raw.get("stale_check", "warn")),
        llm=LlmConfig(
            enabled=bool(llm_raw.get("enabled", False)),
            model=str(llm_raw.get("model", "gpt-4o-mini")),
            max_tokens=int(llm_raw.get("max_tokens", 512)),
        ),
        preserve_sections=bool(raw.get("preserve_sections", True)),
    )
