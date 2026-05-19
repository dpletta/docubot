#!/usr/bin/env bash
# Resolve docubot executable for Cursor project hooks (cwd = repo root).

set -euo pipefail

docubot_resolve() {
  local root="${DOCUBOT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
  export PATH="${root}/.venv/bin:${HOME}/.local/bin:${PATH}"
  if command -v docubot >/dev/null 2>&1; then
    echo "docubot"
    return 0
  fi
  if [[ -x "${root}/.venv/bin/docubot" ]]; then
    echo "${root}/.venv/bin/docubot"
    return 0
  fi
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/docubot" ]]; then
    echo "${VIRTUAL_ENV}/bin/docubot"
    return 0
  fi
  # Editable install from repo without venv on PATH
  if [[ -f "${root}/src/docubot/cli.py" ]]; then
    echo "__py_module__"
    return 0
  fi
  return 1
}

docubot_run() {
  local bin
  if ! bin="$(docubot_resolve)"; then
    if [[ "${DOCUBOT_STRICT:-0}" == "1" ]]; then
      exit 1
    fi
    exit 0
  fi
  if [[ "$bin" == "__py_module__" ]]; then
    local root="${DOCUBOT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
    PYTHONPATH="${root}/src" python3 -m docubot "$@"
  else
    "$bin" "$@"
  fi
}
