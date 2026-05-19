"""Session lifecycle: start, track, finalize, sync."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from docubot.architecture import sync_architecture
from docubot.changelog import append_session_summary, ensure_changelog, sync_commits
from docubot.components import components_for_files
from docubot.config import Config, load_config
from docubot.fingerprint import fingerprint_file
from docubot.git_util import (
    changed_files_since,
    commits_since,
    current_branch,
    dirty_files,
    head_commit,
)
from docubot.metadata.compliance import (
    compliance_context_warnings,
    scaffold_compliance_files,
    sync_compliance_artifacts,
)
from docubot.paths import find_repo_root
from docubot.providers.base import get_provider
from docubot.readme import ensure_readme, update_recent_sessions
from docubot.scaffold import scaffold_docs
from docubot.stale import check_stale
from docubot.state import (
    ActiveSession,
    Manifest,
    SessionRecord,
    delete_active_session,
    finalize_key,
    load_active_session,
    load_manifest,
    new_session_id,
    save_active_session,
    save_manifest,
)


def _repo_root(cwd: Path | None = None) -> Path:
    return find_repo_root(cwd)


def workspace_init(cwd: Path | None = None) -> dict[str, Any]:
    root = _repo_root(cwd)
    config = load_config(root)
    created = scaffold_docs(root, project_name=root.name)
    created.extend(scaffold_compliance_files(root, config, root.name))
    manifest = load_manifest(root)
    save_manifest(root, manifest)
    stale = check_stale(root, config, manifest)
    return {
        "repo_root": str(root),
        "created": created,
        "stale": stale.stale,
        "stale_reason": stale.reason,
    }


def session_start_from_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    payload: dict[str, Any] = json.loads(raw) if raw.strip() else {}
    return session_start(payload)


def session_start(payload: dict[str, Any]) -> dict[str, Any]:
    root = _repo_root()
    config = load_config(root)
    scaffold_docs(root, project_name=root.name)
    scaffold_compliance_files(root, config, root.name)

    conversation_id = payload.get("conversation_id")
    generation_id = payload.get("generation_id")
    manifest = load_manifest(root)

    session_id = new_session_id()
    branch = current_branch(root)
    session = ActiveSession(
        id=session_id,
        conversation_id=conversation_id,
        generation_id=generation_id,
        started_at=_iso_now(),
        branch=branch,
    )
    save_active_session(root, session)
    manifest.active_session_id = session_id
    save_manifest(root, manifest)

    stale = check_stale(root, config, manifest)
    context_lines = [
        f"Docubot session {session_id[:8]} started on branch `{branch or 'unknown'}`.",
    ]
    if stale.stale:
        context_lines.append(f"Warning: documentation may be stale — {stale.reason}")
        if stale.changed_files:
            context_lines.append("Changed: " + ", ".join(stale.changed_files[:10]))
    dirty = dirty_files(root)
    if dirty:
        context_lines.append(f"Uncommitted files: {len(dirty)}")
    for w in compliance_context_warnings(root, config, manifest):
        context_lines.append(f"Compliance: {w}")

    return {
        "session_id": session_id,
        "additional_context": "\n".join(context_lines),
    }


def session_track(file_path: str, cwd: Path | None = None) -> None:
    root = _repo_root(cwd)
    manifest = load_manifest(root)
    sid = manifest.active_session_id
    if not sid:
        return
    session = load_active_session(root, sid)
    if not session:
        return
    rel = _relative_path(root, file_path)
    if rel and rel not in session.files_touched:
        session.files_touched.append(rel)
    session.events.append({"type": "edit", "file": rel})
    save_active_session(root, session)


def session_track_from_stdin() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return
    payload = json.loads(raw)
    fp = payload.get("file_path", "")
    session_track(fp)


def _iso_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _relative_path(root: Path, file_path: str) -> str:
    p = Path(file_path)
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except ValueError:
        return file_path.replace("\\", "/")


def sync_docs(
    repo_root: Path,
    config: Config,
    manifest: Manifest,
    *,
    session: ActiveSession | None = None,
    reason: str | None = None,
    close_session: bool = False,
) -> Manifest:
    """Sync changelog, architecture, readme; update manifest."""
    chg_path = config.changelog_path(repo_root)
    arch_path = config.architecture_path(repo_root)
    readme_path = config.readme_path(repo_root)

    ensure_changelog(chg_path)
    ensure_readme(readme_path, project_name=repo_root.name)

    since = manifest.last_sync_commit
    commits = commits_since(repo_root, since)
    sync_commits(chg_path, commits)

    files = list(session.files_touched) if session else []
    if not files:
        files = changed_files_since(repo_root, since)
    dirty = dirty_files(repo_root)
    for f in dirty:
        if f not in files:
            files.append(f)

    commit_shas = [c.sha for c in commits]
    components = components_for_files(config, files)

    summary: str | None = None
    provider = get_provider(config.llm.enabled)
    if session and (config.llm.enabled or provider.__class__.__name__ != "NoOpProvider"):
        ctx = (
            f"Branch: {session.branch}\n"
            f"Files: {', '.join(files[:30])}\n"
            f"Commits: {len(commit_shas)}\n"
            f"Components: {', '.join(components)}"
        )
        summary = provider.summarize(ctx, max_tokens=config.llm.max_tokens) or None

    if session:
        sync_architecture(
            arch_path,
            config,
            session_id=session.id,
            branch=session.branch,
            files=files,
            commit_count=len(commit_shas),
            summary=summary,
        )
    else:
        from docubot.architecture import ensure_architecture

        ensure_architecture(arch_path)

    if close_session and session:
        record = SessionRecord(
            id=session.id,
            started_at=session.started_at,
            conversation_id=session.conversation_id,
            ended_at=_iso_now(),
            reason=reason,
            branch=session.branch,
            commits=commit_shas,
            files_touched=files,
            components_touched=components,
            summary=summary,
        )
        manifest.sessions.append(record)
        if summary:
            append_session_summary(chg_path, summary, session.id)
        manifest.active_session_id = None
        delete_active_session(repo_root, session.id)

    update_recent_sessions(readme_path, manifest.sessions)

    if config.compliance.nih_dms or config.compliance.fair:
        manifest, _ = sync_compliance_artifacts(repo_root, config, manifest, files)

    head = head_commit(repo_root)
    if head:
        manifest.last_sync_commit = head
    manifest.last_sync_at = _iso_now()

    doc_paths = [
        config.docs.changelog,
        config.docs.architecture,
        config.docs.readme,
        config.docs.dms_plan,
        config.docs.fair_checklist,
        config.metadata.datacite_output,
    ]
    for doc_rel in doc_paths:
        fp = repo_root / doc_rel
        if fp.is_file():
            digest = fingerprint_file(fp)
            if digest:
                manifest.doc_fingerprints[doc_rel] = digest

    return manifest


def session_finalize(
    reason: str = "session_end",
    *,
    conversation_id: str | None = None,
    generation_id: str | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(cwd)
    config = load_config(root)
    manifest = load_manifest(root)

    key = finalize_key(conversation_id, generation_id, reason)
    if key in manifest.finalize_keys:
        return {"status": "skipped", "reason": "already_finalized", "key": key}

    session: ActiveSession | None = None
    sid = manifest.active_session_id
    if sid:
        session = load_active_session(root, sid)

    if session and conversation_id and not session.conversation_id:
        session.conversation_id = conversation_id

    manifest = sync_docs(
        root,
        config,
        manifest,
        session=session,
        reason=reason,
        close_session=bool(session),
    )

    manifest.finalize_keys.append(key)
    if len(manifest.finalize_keys) > 100:
        manifest.finalize_keys = manifest.finalize_keys[-50:]
    save_manifest(root, manifest)

    return {
        "status": "ok",
        "reason": reason,
        "session_closed": sid is not None,
        "last_sync_commit": manifest.last_sync_commit,
    }


def session_finalize_from_stdin(reason: str) -> dict[str, Any]:
    raw = sys.stdin.read()
    payload: dict[str, Any] = json.loads(raw) if raw.strip() else {}
    return session_finalize(
        reason=reason,
        conversation_id=payload.get("conversation_id"),
        generation_id=payload.get("generation_id"),
    )
