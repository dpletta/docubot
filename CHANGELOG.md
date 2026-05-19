# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
