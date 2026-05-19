# docubot

<!-- docubot:overview -->
Portable hook-driven documentation agent for AI-assisted development and data science workflows. Keeps `CHANGELOG.md`, `docs/ARCHITECTURE.md`, and `README.md` in sync with git history and your coding sessions.
<!-- /docubot:overview -->

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

docubot init
docubot status
```

### Cursor integration

Project hooks in [`.cursor/hooks.json`](.cursor/hooks.json) run automatically in trusted workspaces:

| Hook | Action |
|------|--------|
| `workspaceOpen` | Initialize docs and manifest |
| `sessionStart` | Start session; inject stale-doc context |
| `afterFileEdit` | Track edited files |
| `sessionEnd` / `stop` | Finalize session and sync docs |

### Git hooks (optional)

```bash
docubot install --git-hooks
```

Installs [`.githooks/`](.githooks/) and sets `core.hooksPath` for changelog sync and stale-doc reminders.

## CLI

| Command | Description |
|---------|-------------|
| `docubot init` | Scaffold templates and manifest |
| `docubot workspace init` | Workspace-open hook entrypoint |
| `docubot session start` | Begin a coding session |
| `docubot session track --file PATH` | Record a file edit |
| `docubot session finalize` | Sync docs and close session |
| `docubot sync` | Sync without closing session |
| `docubot status` | Staleness and session info |
| `docubot validate` | CI check (exit 1 if stale in strict mode) |

## Configuration

See [`.docubot/config.yaml`](.docubot/config.yaml) for watch paths, component rules, and LLM settings.

Optional LLM (off by default):

```bash
export DOCUBOT_LLM_API_KEY=...
export DOCUBOT_LLM_BASE_URL=https://api.openai.com/v1
# Enable in .docubot/config.yaml: llm.enabled: true
```

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — [Keep a Changelog](https://keepachangelog.com/)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — living architecture reference

## Recent Sessions

<!-- docubot:recent-sessions -->
- **2026-05-19** `fc67abe4` (cursor/docubot-agent-72b2): 13 files, 0 commits, components: core, hooks, docs. Ended: 2026-05-19T17:26:11Z
<!-- /docubot:recent-sessions -->

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## License

MIT — see [LICENSE](LICENSE).
