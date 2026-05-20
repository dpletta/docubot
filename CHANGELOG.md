# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Core performance: batched `git log`, conditional compliance sync, stat-based doc fingerprints, faster session track/start

### Changed

- `session_track` no longer appends unbounded per-edit events; session files use compact JSON

- FAIR checklist and DataCite-compatible `metadata/datacite.json` generation
- NIH Data Management and Sharing Plan scaffold (`docs/DATA_MANAGEMENT_AND_SHARING.md`, NOT-OD-21-014)
- Project metadata source of truth (`.docubot/metadata/project.yaml`)
- `docubot validate --compliance` for FAIR/NIH field checks
- README compliance status block; session context compliance warnings
- Initial docubot package: hook-driven documentation agent for Cursor and git
- Python CLI (`docubot init`, `session`, `sync`, `status`, `validate`, `install`)
- Cursor lifecycle hooks (`workspaceOpen`, `sessionStart`, `afterFileEdit`, `sessionEnd`, `stop`)
- Optional git hooks (`.githooks/`) for changelog sync on commit
- Keep a Changelog–compatible `CHANGELOG.md` maintenance
- Living `docs/ARCHITECTURE.md` with session activity tracking
- README managed blocks for recent sessions
- Manifest-based staleness detection (`.docubot/manifest.json`)
- Optional OpenAI-compatible LLM summaries (disabled by default)

### Changed

### Fixed
