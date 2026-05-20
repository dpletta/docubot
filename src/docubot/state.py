"""Manifest and per-session state persistence."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from docubot.paths import manifest_path, sessions_dir


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class SessionRecord:
    id: str
    started_at: str
    conversation_id: str | None = None
    ended_at: str | None = None
    reason: str | None = None
    branch: str | None = None
    commits: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)
    components_touched: list[str] = field(default_factory=list)
    summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionRecord:
        return cls(
            id=data["id"],
            started_at=data["started_at"],
            conversation_id=data.get("conversation_id"),
            ended_at=data.get("ended_at"),
            reason=data.get("reason"),
            branch=data.get("branch"),
            commits=list(data.get("commits") or []),
            files_touched=list(data.get("files_touched") or []),
            components_touched=list(data.get("components_touched") or []),
            summary=data.get("summary"),
        )


@dataclass
class ComplianceState:
    fair_last_assessed: str | None = None
    nih_dms_last_synced: str | None = None
    citation_cff_last_synced: str | None = None
    fair_score: dict[str, int] = field(default_factory=dict)
    validation_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceState:
        return cls(
            fair_last_assessed=data.get("fair_last_assessed"),
            nih_dms_last_synced=data.get("nih_dms_last_synced"),
            citation_cff_last_synced=data.get("citation_cff_last_synced"),
            fair_score=dict(data.get("fair_score") or {}),
            validation_warnings=list(data.get("validation_warnings") or []),
        )


@dataclass
class Manifest:
    schema_version: int = 1
    last_sync_commit: str | None = None
    last_sync_at: str | None = None
    doc_fingerprints: dict[str, str] = field(default_factory=dict)
    active_session_id: str | None = None
    sessions: list[SessionRecord] = field(default_factory=list)
    finalize_keys: list[str] = field(default_factory=list)
    compliance: ComplianceState | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "last_sync_commit": self.last_sync_commit,
            "last_sync_at": self.last_sync_at,
            "doc_fingerprints": self.doc_fingerprints,
            "active_session_id": self.active_session_id,
            "sessions": [s.to_dict() for s in self.sessions],
            "finalize_keys": self.finalize_keys,
        }
        if self.compliance is not None:
            out["compliance"] = self.compliance.to_dict()
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        sessions = [
            SessionRecord.from_dict(s) for s in (data.get("sessions") or []) if isinstance(s, dict)
        ]
        comp_raw = data.get("compliance")
        compliance = (
            ComplianceState.from_dict(comp_raw) if isinstance(comp_raw, dict) else None
        )
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            last_sync_commit=data.get("last_sync_commit"),
            last_sync_at=data.get("last_sync_at"),
            doc_fingerprints=dict(data.get("doc_fingerprints") or {}),
            active_session_id=data.get("active_session_id"),
            sessions=sessions,
            finalize_keys=list(data.get("finalize_keys") or []),
            compliance=compliance,
        )


def load_manifest(repo_root: Path) -> Manifest:
    path = manifest_path(repo_root)
    if not path.is_file():
        return Manifest()
    return Manifest.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_manifest(repo_root: Path, manifest: Manifest) -> None:
    path = manifest_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")


@dataclass
class ActiveSession:
    """Ephemeral session state (gitignored)."""

    id: str
    conversation_id: str | None
    generation_id: str | None
    started_at: str
    branch: str | None
    files_touched: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActiveSession:
        return cls(
            id=data["id"],
            conversation_id=data.get("conversation_id"),
            generation_id=data.get("generation_id"),
            started_at=data["started_at"],
            branch=data.get("branch"),
            files_touched=list(data.get("files_touched") or []),
            events=list(data.get("events") or []),
        )


def session_file(repo_root: Path, session_id: str) -> Path:
    return sessions_dir(repo_root) / f"{session_id}.json"


def load_active_session(repo_root: Path, session_id: str) -> ActiveSession | None:
    path = session_file(repo_root, session_id)
    if not path.is_file():
        return None
    return ActiveSession.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_active_session(repo_root: Path, session: ActiveSession) -> None:
    sessions_dir(repo_root).mkdir(parents=True, exist_ok=True)
    session_file(repo_root, session.id).write_text(
        json.dumps(session.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def delete_active_session(repo_root: Path, session_id: str) -> None:
    path = session_file(repo_root, session_id)
    if path.is_file():
        path.unlink()


def new_session_id() -> str:
    return str(uuid.uuid4())


def finalize_key(conversation_id: str | None, generation_id: str | None, reason: str) -> str:
    return f"{conversation_id or 'none'}:{generation_id or 'none'}:{reason}"
