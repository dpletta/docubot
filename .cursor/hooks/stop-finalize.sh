#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export DOCUBOT_ROOT="$ROOT"
source "$ROOT/.cursor/hooks/common.sh"
docubot_run session finalize --reason=agent_stop --json-stdin || true
exit 0
