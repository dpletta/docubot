#!/bin/bash
# Install docubot and its dev dependencies so tests and linters work in
# Claude Code on the web. Idempotent: safe to re-run.
set -euo pipefail

# Only run inside the managed remote environment; locally the developer
# is responsible for their own virtualenv.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

python -m pip install --quiet -e ".[dev]"

# Make `docubot` discoverable on PATH for future hook runs.
USER_BIN="$(python -c 'import site,sys; print(site.getuserbase())')/bin"
if [ -d "$USER_BIN" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$USER_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
