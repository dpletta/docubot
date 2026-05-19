"""Docubot CLI entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click

from docubot.changelog import append_commit_entry, ensure_changelog
from docubot.config import load_config
from docubot.git_util import get_commit, head_commit, is_git_repo
from docubot.paths import find_repo_root
from docubot.scaffold import install_cursor_hooks, install_git_hooks, scaffold_docs
from docubot.session import (
    session_finalize,
    session_finalize_from_stdin,
    session_start,
    session_start_from_stdin,
    session_track,
    session_track_from_stdin,
    sync_docs,
    workspace_init,
)
from docubot.stale import check_stale
from docubot.state import load_active_session, load_manifest, save_manifest


def _repo_root() -> Path:
    return find_repo_root()


@click.group()
@click.version_option(package_name="docubot")
def main() -> None:
    """Portable documentation agent for AI-assisted development."""


@main.command("init")
@click.option("--project-name", default=None, help="Project name for README template")
def cmd_init(project_name: str | None) -> None:
    """Scaffold docs, config, and hook wiring."""
    root = _repo_root()
    name = project_name or root.name
    created = scaffold_docs(root, project_name=name)
    install_cursor_hooks(root)
    click.echo(f"Initialized docubot in {root}")
    if created:
        click.echo("Created: " + ", ".join(created))


@main.group()
def workspace() -> None:
    """Workspace lifecycle commands."""


@workspace.command("init")
def cmd_workspace_init() -> None:
    """Run on workspace open (Cursor workspaceOpen hook)."""
    result = workspace_init()
    click.echo(json.dumps(result))


@main.group()
def session() -> None:
    """Coding session lifecycle."""


@session.command("start")
@click.option("--json-stdin", is_flag=True, default=False, help="Read hook JSON from stdin")
def cmd_session_start(json_stdin: bool) -> None:
    """Start a new coding session."""
    if json_stdin or not sys.stdin.isatty():
        result = session_start_from_stdin()
    else:
        result = session_start({})
    # Cursor sessionStart may read additional_context from stdout
    if result.get("additional_context"):
        click.echo(json.dumps({"additional_context": result["additional_context"]}))
    else:
        click.echo(json.dumps(result))


@session.command("track")
@click.option("--file", "file_path", required=True, help="Edited file path")
def cmd_session_track(file_path: str) -> None:
    """Record a file edit during the active session."""
    session_track(file_path)


@session.command("track-stdin")
def cmd_session_track_stdin() -> None:
    """Record edit from afterFileEdit hook JSON on stdin."""
    session_track_from_stdin()


@session.command("finalize")
@click.option("--reason", default="manual", help="Finalize reason for idempotency")
@click.option("--json-stdin", is_flag=True, default=False, help="Read hook JSON from stdin")
def cmd_session_finalize(reason: str, json_stdin: bool) -> None:
    """Finalize session and sync all documentation."""
    if json_stdin or not sys.stdin.isatty():
        result = session_finalize_from_stdin(reason)
    else:
        result = session_finalize(reason=reason)
    click.echo(json.dumps(result))


@main.command("sync")
def cmd_sync() -> None:
    """Sync documentation without closing the active session."""
    root = _repo_root()
    config = load_config(root)
    manifest = load_manifest(root)
    session = None
    if manifest.active_session_id:
        session = load_active_session(root, manifest.active_session_id)
    manifest = sync_docs(root, config, manifest, session=session, close_session=False)
    save_manifest(root, manifest)
    click.echo(f"Synced docs at commit {manifest.last_sync_commit or 'n/a'}")


@main.command("status")
def cmd_status() -> None:
    """Show docubot status and staleness."""
    root = _repo_root()
    config = load_config(root)
    manifest = load_manifest(root)
    stale = check_stale(root, config, manifest)
    click.echo(f"Repository: {root}")
    click.echo(f"Last sync commit: {manifest.last_sync_commit or 'never'}")
    click.echo(f"Last sync at: {manifest.last_sync_at or 'never'}")
    click.echo(f"Active session: {manifest.active_session_id or 'none'}")
    click.echo(f"Sessions recorded: {len(manifest.sessions)}")
    if stale.stale:
        click.echo(f"Stale: yes — {stale.reason}")
        for f in stale.changed_files[:20]:
            click.echo(f"  - {f}")
    else:
        click.echo("Stale: no")


@main.command("validate")
@click.pass_context
def cmd_validate(ctx: click.Context) -> None:
    """Exit 1 if documentation is stale (for CI)."""
    root = _repo_root()
    config = load_config(root)
    manifest = load_manifest(root)
    stale = check_stale(root, config, manifest)
    if stale.stale and config.stale_check in ("strict", "warn"):
        if config.stale_check == "strict":
            click.echo(f"Documentation stale: {stale.reason}", err=True)
            ctx.exit(1)
        click.echo(f"Warning: {stale.reason}", err=True)
    click.echo("OK")


@main.command("install")
@click.option("--git-hooks", is_flag=True, help="Install .githooks and set core.hooksPath")
def cmd_install(git_hooks: bool) -> None:
    """Install optional integrations."""
    root = _repo_root()
    install_cursor_hooks(root)
    click.echo("Cursor hooks: .cursor/hooks.json")
    if git_hooks:
        hooks_dir = install_git_hooks(root)
        subprocess.run(
            ["git", "-C", str(root), "config", "core.hooksPath", str(hooks_dir)],
            check=True,
        )
        click.echo(f"Git hooks installed at {hooks_dir}")


@main.group()
def git() -> None:
    """Git hook helpers."""


@git.command("post-commit")
def cmd_git_post_commit() -> None:
    """Append changelog entry for HEAD commit."""
    root = _repo_root()
    config = load_config(root)
    if not is_git_repo(root):
        return
    sha = head_commit(root)
    if not sha:
        return
    commit = get_commit(root, sha)
    if not commit:
        return
    path = config.changelog_path(root)
    ensure_changelog(path)
    if append_commit_entry(path, commit):
        click.echo(f"Updated {path.name} for {commit.short}", err=True)


@git.command("pre-commit")
@click.pass_context
def cmd_git_pre_commit(ctx: click.Context) -> None:
    """Block commit if docs are stale (strict mode only)."""
    root = _repo_root()
    config = load_config(root)
    if config.stale_check != "strict":
        return
    manifest = load_manifest(root)
    stale = check_stale(root, config, manifest)
    if stale.stale:
        click.echo(
            f"docubot: documentation stale — run 'docubot sync' before committing.\n"
            f"  {stale.reason}",
            err=True,
        )
        ctx.exit(1)


@git.command("prepare-commit-msg")
@click.argument("commit_msg_file", type=click.Path(path_type=Path))
@click.argument("commit_source", required=False)
@click.argument("sha1", required=False)
def cmd_prepare_commit_msg(
    commit_msg_file: Path,
    commit_source: str | None,
    sha1: str | None,
) -> None:
    """Add stale-doc reminder comment to commit message template."""
    root = _repo_root()
    config = load_config(root)
    if config.stale_check == "off":
        return
    manifest = load_manifest(root)
    stale = check_stale(root, config, manifest)
    if not stale.stale:
        return
    text = commit_msg_file.read_text(encoding="utf-8")
    reminder = f"\n# docubot: docs may be stale — {stale.reason}\n"
    if "docubot:" not in text:
        commit_msg_file.write_text(text + reminder, encoding="utf-8")


if __name__ == "__main__":
    main()
