# AGENTS.md

## Cursor Cloud specific instructions

**docubot** is a Python CLI tool (Click-based) for automated documentation management. No Docker, databases, or external services are required.

### Key commands

| Task | Command |
|------|---------|
| Install deps | `pip install -e ".[dev]"` |
| Lint | `ruff check src tests` |
| Tests | `pytest -q` |
| Validate docs | `docubot validate` |
| Validate compliance | `docubot validate --compliance all` |

### Gotchas

- The `docubot` CLI is installed to `~/.local/bin`. Ensure `$HOME/.local/bin` is on `PATH`.
- `docubot session start` reads JSON from stdin when stdin is not a TTY (i.e. in shell pipelines). Pipe `echo '{}' | docubot session start` to avoid hanging. Same applies to `session finalize` and `session track-stdin`.
- LLM features are disabled by default (`NoOpProvider`). No API key is needed for tests or normal operation.
- All tests run locally with `pytest` and complete in under 1 second. No mocking of external services is needed beyond what the test suite already provides.
