#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Rico 4.0 System Stopper
# -----------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs"
BACKEND_PID="$LOG_DIR/backend.pid"
FRONTEND_PID="$LOG_DIR/frontend.pid"

# Helper-Funktionen
msg()  { echo -e "• $*"; }
ok()   { echo -e "✓ $*"; }
fail() { echo -e "✖ $*" >&2; }

echo "🛑 Rico 4.0 System stoppen..."

# PID-basiertes Stoppen (sanft)
kill_by_pid() {
  local pid_file="$1"
  local service="$2"
  if [[ -f "$pid_file" ]]; then
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      msg "Stoppe ${service} (PID: $pid) …"
      kill -TERM "$pid" 2>/dev/null || true
      sleep 3
      if kill -0 "$pid" 2>/dev/null; then
        msg "Force-kill ${service} (PID: $pid) …"
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pid_file"
  fi
}

# Services stoppen
kill_by_pid "$BACKEND_PID" "Backend"
kill_by_pid "$FRONTEND_PID" "Frontend"

# Fallback: Alle Rico-Prozesse stoppen
msg "Stoppe alle Rico-Prozesse …"
pkill -f "uvicorn app.main:app" || true
pkill -f "streamlit run" || true

# Ports freimachen
msg "Räume Ports auf …"
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :8501 | xargs kill -9 2>/dev/null || true
lsof -ti :8502 | xargs kill -9 2>/dev/null || true

ok "Alle Services gestoppt."