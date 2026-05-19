# Architecture

<!-- docubot:managed -->

## Overview

_Describe the system purpose and high-level design._

## Context

```mermaid
flowchart LR
  User[Developer] --> IDE[Cursor / IDE]
  IDE --> Docubot[Docubot Hooks]
  Docubot --> Docs[Documentation Artifacts]
  Docubot --> Git[Git Repository]
```

## Components

| Component | Responsibility | Paths |
|-----------|----------------|-------|
| _name_ | _description_ | _globs_ |

## Data Flow

1. Workspace opens → docubot initializes templates and manifest.
2. Coding session starts → session state tracks edits and commits.
3. Session ends → changelog, architecture, and README sync from git history.

## Key Decisions

- Documentation is hook-driven and deterministic by default.
- Optional LLM enrichment is behind explicit configuration.

## Dependencies

- Python 3.11+
- Git
- Cursor hooks (optional; git hooks available as fallback)

## Session Activity

<!-- docubot:session-activity -->
_No sessions recorded yet._
<!-- /docubot:session-activity -->
