#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export DOCUBOT_ROOT="$ROOT"
source "$ROOT/.cursor/hooks/common.sh"
cat >/dev/null || true
docubot_run workspace init || true
exit 0
