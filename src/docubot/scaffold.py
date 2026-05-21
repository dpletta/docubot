"""Initialize project files and templates."""

from __future__ import annotations

import json
from pathlib import Path

from docubot.architecture import ensure_architecture
from docubot.changelog import ensure_changelog
from docubot.config import load_config
from docubot.metadata.compliance import scaffold_compliance_files
from docubot.paths import docubot_dir, manifest_path, templates_dir
from docubot.readme import ensure_readme
from docubot.state import Manifest, save_manifest


def _read_template(repo_root: Path, name: str) -> str | None:
    path = templates_dir(repo_root) / name
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def scaffold_docs(repo_root: Path, project_name: str = "docubot") -> list[str]:
    created: list[str] = []
    tpl_chg = _read_template(repo_root, "CHANGELOG.md.tpl")
    tpl_arch = _read_template(repo_root, "ARCHITECTURE.md.tpl")
    tpl_readme = _read_template(repo_root, "README.md.tpl")

    chg = repo_root / "CHANGELOG.md"
    if not chg.is_file():
        ensure_changelog(chg, tpl_chg)
        created.append(str(chg.relative_to(repo_root)))

    arch = repo_root / "docs" / "ARCHITECTURE.md"
    if not arch.is_file():
        ensure_architecture(arch, tpl_arch)
        created.append(str(arch.relative_to(repo_root)))

    readme = repo_root / "README.md"
    if not readme.is_file():
        ensure_readme(readme, tpl_readme, project_name=project_name)
        created.append(str(readme.relative_to(repo_root)))

    docubot_dir(repo_root).mkdir(parents=True, exist_ok=True)

    if not manifest_path(repo_root).is_file():
        save_manifest(repo_root, Manifest())
        created.append(".docubot/manifest.json")

    config = load_config(repo_root)
    created.extend(scaffold_compliance_files(repo_root, config, project_name))

    return created


def install_cursor_hooks(repo_root: Path) -> None:
    """Ensure .cursor/hooks exist (committed in repo)."""
    hooks_json = repo_root / ".cursor" / "hooks.json"
    if not hooks_json.is_file():
        hooks_json.parent.mkdir(parents=True, exist_ok=True)
        hooks_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "workspaceOpen": [{"command": ".cursor/hooks/workspace-open.sh"}],
                        "sessionStart": [{"command": ".cursor/hooks/session-start.sh"}],
                        "afterFileEdit": [{"command": ".cursor/hooks/session-track-edit.sh"}],
                        "sessionEnd": [{"command": ".cursor/hooks/session-end.sh"}],
                        "stop": [{"command": ".cursor/hooks/stop-finalize.sh"}],
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def install_git_hooks(repo_root: Path) -> Path:
    githooks = repo_root / ".githooks"
    githooks.mkdir(parents=True, exist_ok=True)
    for name in ("post-commit", "pre-commit", "prepare-commit-msg"):
        src = repo_root / ".githooks" / name
        if not src.is_file():
            _write_git_hook(src, name)
        src.chmod(0o755)
    return githooks


def _write_git_hook(path: Path, name: str) -> None:
    if name == "post-commit":
        body = """#!/bin/sh
# Docubot post-commit: sync changelog from commit message
ROOT="$(git rev-parse --show-toplevel)"
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$PATH"
if command -v docubot >/dev/null 2>&1; then
  docubot git post-commit
elif [ -x "$ROOT/.venv/bin/docubot" ]; then
  "$ROOT/.venv/bin/docubot" git post-commit
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH="$ROOT/src" python3 -m docubot.cli git post-commit 2>/dev/null || true
fi
"""
    elif name == "pre-commit":
        body = """#!/bin/sh
ROOT="$(git rev-parse --show-toplevel)"
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$PATH"
if command -v docubot >/dev/null 2>&1; then
  docubot git pre-commit || exit $?
elif [ -x "$ROOT/.venv/bin/docubot" ]; then
  "$ROOT/.venv/bin/docubot" git pre-commit || exit $?
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH="$ROOT/src" python3 -m docubot.cli git pre-commit || exit $?
fi
"""
    else:
        body = """#!/bin/sh
ROOT="$(git rev-parse --show-toplevel)"
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$PATH"
if command -v docubot >/dev/null 2>&1; then
  docubot git prepare-commit-msg "$1" "$2" "$3"
elif [ -x "$ROOT/.venv/bin/docubot" ]; then
  "$ROOT/.venv/bin/docubot" git prepare-commit-msg "$1" "$2" "$3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH="$ROOT/src" python3 -m docubot.cli \\
    git prepare-commit-msg "$1" "$2" "$3" 2>/dev/null || true
fi
"""
    path.write_text(body, encoding="utf-8")
