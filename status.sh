#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Rico 4.0 System Status
# -----------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs"
BACKEND_PID="$LOG_DIR/backend.pid"
FRONTEND_PID="$LOG_DIR/frontend.pid"

# Helper-Funktionen
msg()  { echo -e "• $*"; }
ok()   { echo -e "✓ $*"; }
fail() { echo -e "✖ $*"; }
warn() { echo -e "⚠ $*"; }

echo "🔍 Rico 4.0 System Status"
echo "========================="

# PID-Status prüfen
check_pid() {
  local pid_file="$1"
  local service="$2"
  if [[ -f "$pid_file" ]]; then
    local pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      ok "${service}: Läuft (PID: $pid)"
      return 0
    else
      fail "${service}: PID-Datei vorhanden, aber Prozess nicht aktiv"
      return 1
    fi
  else
    fail "${service}: Nicht gestartet (keine PID-Datei)"
    return 1
  fi
}

# Port-Status prüfen
check_port() {
  local port="$1"
  local service="$2"
  if lsof -ti tcp:"$port" >/dev/null 2>&1; then
    local pid=$(lsof -ti tcp:"$port")
    ok "${service}: Port ${port} belegt (PID: $pid)"
    return 0
  else
    fail "${service}: Port ${port} frei"
    return 1
  fi
}

# URL-Status prüfen
check_url() {
  local url="$1"
  local service="$2"
  if curl -s -m 3 "$url" >/dev/null 2>&1; then
    ok "${service}: ${url} erreichbar"
    return 0
  else
    fail "${service}: ${url} nicht erreichbar"
    return 1
  fi
}

echo ""
msg "Service-Status:"
check_pid "$BACKEND_PID" "Backend"
check_pid "$FRONTEND_PID" "Frontend"

echo ""
msg "Port-Status:"
check_port 8000 "Backend"
check_port 8501 "Frontend"

echo ""
msg "URL-Status:"
check_url "http://127.0.0.1:8000" "Backend"
check_url "http://127.0.0.1:8501" "Frontend"

echo ""
msg "API-Endpoints:"
check_url "http://127.0.0.1:8000/check-keys" "Health-Check"
check_url "http://127.0.0.1:8000/v2/core/prompts" "v2/core API"

echo ""
msg "Log-Dateien:"
if [[ -f "$LOG_DIR/backend.log" ]]; then
  backend_size=$(wc -l < "$LOG_DIR/backend.log" 2>/dev/null || echo "0")
  echo "  Backend:  $LOG_DIR/backend.log ($backend_size Zeilen)"
else
  warn "Backend-Log nicht gefunden"
fi

if [[ -f "$LOG_DIR/frontend.log" ]]; then
  frontend_size=$(wc -l < "$LOG_DIR/frontend.log" 2>/dev/null || echo "0")
  echo "  Frontend: $LOG_DIR/frontend.log ($frontend_size Zeilen)"
else
  warn "Frontend-Log nicht gefunden"
fi

echo ""
echo "🎯 Quick Actions:"
echo "  Start:   ./start.sh"
echo "  Stop:    ./stop.sh"
echo "  Logs:    tail -f $LOG_DIR/backend.log"
echo "  Logs:    tail -f $LOG_DIR/frontend.log"
echo "  System:  http://127.0.0.1:8501 → System Tab"
