#!/usr/bin/env bash
# HeartBuddy 一键启动：同时拉起后端(8000) + 前端(5173)
# 用法：./start.sh   停止：./stop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p logs

BACKEND_PORT=8000
FRONTEND_PORT=5173

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti ":$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "  端口 $port 已被占用，清理旧进程: $pids"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

echo "▶ 清理旧进程…"
kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

echo "▶ 启动后端 (uvicorn --reload, :$BACKEND_PORT)…"
nohup python3 -m uvicorn backend.main:app \
  --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
  > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

echo "▶ 启动前端 (vite, :$FRONTEND_PORT)…"
( cd frontend && nohup npm run dev > "$ROOT/logs/frontend.log" 2>&1 & echo $! > "$ROOT/logs/frontend.pid" )

# 等待就绪
sleep 4
echo ""
if lsof -ti ":$BACKEND_PORT" >/dev/null 2>&1; then
  echo "✅ 后端  http://localhost:$BACKEND_PORT   (日志: logs/backend.log)"
else
  echo "❌ 后端启动失败，见 logs/backend.log"; tail -5 logs/backend.log
fi
if lsof -ti ":$FRONTEND_PORT" >/dev/null 2>&1; then
  echo "✅ 前端  http://localhost:$FRONTEND_PORT   (日志: logs/frontend.log)"
else
  echo "❌ 前端启动失败，见 logs/frontend.log"; tail -5 logs/frontend.log
fi
echo ""
echo "停止全部：./stop.sh"
