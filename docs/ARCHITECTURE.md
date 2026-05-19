# Architecture

<!-- docubot:managed -->

## Overview

Docubot is a portable documentation agent that keeps project docs aligned with git history and coding sessions. It runs via Cursor hooks (primary) and optional git hooks (secondary), using a Python CLI for deterministic updates and optional LLM enrichment.

## Context

```mermaid
flowchart LR
  User[Developer] --> IDE[Cursor IDE]
  IDE --> Hooks[Cursor Hooks]
  Hooks --> CLI[docubot CLI]
  CLI --> State[.docubot state]
  CLI --> Git[Git]
  CLI --> Docs[CHANGELOG ARCHITECTURE README]
```

## Components


| Component | Responsibility | Paths |
|-----------|----------------|-------|
| core | _auto-tracked_ | `src/docubot/**` |
| hooks | _auto-tracked_ | `.cursor/hooks/**, .githooks/**` |
| docs | _auto-tracked_ | `docs/**, templates/**, *.md` |

## Data Flow

1. **workspaceOpen** — scaffold missing docs, load manifest.
2. **sessionStart** — create ephemeral session under `.docubot/sessions/`.
3. **afterFileEdit** — queue touched files (fast, no LLM).
4. **sessionEnd / stop** — sync changelog, architecture, README; archive session to manifest.
5. **post-commit** (optional) — append changelog entry from commit message.

## Key Decisions

- Deterministic updates by default; LLM is opt-in via config and environment variables.
- HTML comment blocks protect hand-edited README sections outside managed regions.
- Idempotent finalize via `conversation_id:generation_id:reason` keys in manifest.
- Session files are gitignored; manifest metadata is committed.

## Dependencies

- Python 3.11+
- Git
- PyYAML, Click
- Cursor (for lifecycle hooks; git hooks work elsewhere)

## Session Activity

<!-- docubot:session-activity -->
- **2026-05-19 17:26 UTC** — session `fc67abe4` on branch `cursor/docubot-agent-72b2`: 13 file(s), 0 commit(s), components: core, hooks, docs.
<!-- /docubot:session-activity -->
