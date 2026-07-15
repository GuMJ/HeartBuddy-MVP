#!/usr/bin/env bash
# HeartBuddy 一键停止：关闭后端(8000) + 前端(5173)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kill_port() {
  local port="$1" label="$2" pids
  pids="$(lsof -ti ":$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -9 2>/dev/null || true
    echo "✅ 已停止 $label (:$port) → $pids"
  else
    echo "· $label (:$port) 未在运行"
  fi
}

kill_port 8000 "后端"
kill_port 5173 "前端"
rm -f "$ROOT/logs/backend.pid" "$ROOT/logs/frontend.pid" 2>/dev/null || true
