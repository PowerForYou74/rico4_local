#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Rico 4.0 System Starter

# -----------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# -----------------------------
# ENV Loading
# -----------------------------
echo "[Rico] Loading ENV…"
if [ -f ".env.local" ]; then 
    source .env.local
    ENV_SRC=".env.local"
elif [ -f ".env" ]; then 
    source .env
    ENV_SRC=".env"
else 
    ENV_SRC="environment"
fi
echo "[Rico] ENV source: $ENV_SRC"

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Port-Konfiguration
BACKEND_PORT=8000
FRONTEND_PORT=8501
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

# PID-Dateien
BACKEND_PID="$LOG_DIR/backend.pid"
FRONTEND_PID="$LOG_DIR/frontend.pid"

# -----------------------------
# Helpers
# -----------------------------
msg()  { echo -e "• $*"; }
ok()   { echo -e "✓ $*"; }
fail() { echo -e "✖ $*" >&2; }

# Verbesserte Service-Verwaltung
kill_on_port() {
  local port="$1"
  local service="$2"
  if lsof -ti tcp:"$port" >/dev/null 2>&1; then
    msg "Beende ${service} auf Port ${port} …"
    lsof -ti tcp:"$port" | xargs kill -9 || true
    sleep 2
  fi
}

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

wait_for_url() {
  local url="$1"
  local tries="${2:-60}"
  local i=1
  msg "Warte bis ${url} erreichbar ist …"
  until curl -s -m 1 "${url}" >/dev/null 2>&1; do
    if [[ $i -ge $tries ]]; then
      fail "Timeout: ${url} nicht erreichbar."
      exit 1
    fi
    sleep 1
    ((i++))
  done
  ok "${url} erreichbar."
}

# -----------------------------
# Sanftes Stoppen & Ports freimachen
# -----------------------------
echo "== Rico 4.0 System Starter =="
msg "Prüfe laufende Services …"

# Bestehende Services sauber stoppen
kill_by_pid "$BACKEND_PID" "Backend"
kill_by_pid "$FRONTEND_PID" "Frontend"

# Fallback: Ports freimachen
kill_on_port "${BACKEND_PORT}" "Backend"
kill_on_port "${FRONTEND_PORT}" "Frontend"

# Zusätzliche Streamlit-Prozesse stoppen
msg "Stoppe alle Streamlit-Prozesse …"
pkill -f "streamlit run" || true
sleep 2

# -----------------------------
# venv anlegen/aktivieren
# -----------------------------
if [[ ! -d ".venv" ]]; then
  msg "Erstelle virtuelle Umgebung (.venv) …"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source ".venv/bin/activate"
ok "Python $(python -V) aktiv."

# Abhängigkeiten (optional)
if [[ -f "requirements.txt" ]]; then
  msg "Installiere requirements.txt …"
  pip install -U pip >/dev/null
  pip install -r requirements.txt
else
  # Minimal-Set, falls keine requirements.txt
  msg "Installiere Basis-Pakete …"
  pip install -U pip >/dev/null
  pip install fastapi "uvicorn[standard]" streamlit requests python-dotenv openai anthropic httpx pydantic apscheduler
fi

# -----------------------------
# Backend starten (Uvicorn)
# -----------------------------
msg "Starte Backend (Uvicorn) auf Port ${BACKEND_PORT} …"
mv "$LOG_DIR/backend.log" "$LOG_DIR/backend.log.1" 2>/dev/null || true

# Backend mit verbesserter Konfiguration starten
msg "Starting backend…"
nohup uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port "${BACKEND_PORT}" \
  --app-dir backend \
  --log-level info \
  > "$LOG_DIR/backend.log" 2>&1 & 
echo $! > "$BACKEND_PID"

# -----------------------------
# n8n Bootstrap (wenn aktiviert)
# -----------------------------
if [ "${N8N_ENABLED:-false}" = "true" ]; then
  echo "[Rico] Bootstrapping n8n…"
  if python integrations/n8n/bootstrap.py; then
    ok "n8n bootstrap completed successfully"
  else
    echo "[Rico] n8n bootstrap warning (non-fatal)"
  fi
else
  msg "n8n disabled (N8N_ENABLED != true), skipping bootstrap"
fi

# -----------------------------
# Autopilot Scheduler starten
# -----------------------------
if [ "${AUTOPILOT_ENABLED:-true}" = "true" ]; then
  msg "Starte Autopilot Scheduler…"
  # Autopilot Scheduler wird automatisch beim Backend-Start initialisiert
  ok "Autopilot Scheduler aktiviert"
else
  msg "Autopilot disabled (AUTOPILOT_ENABLED != true), skipping scheduler"
fi

# -----------------------------
# Frontend starten (Streamlit)
# -----------------------------
msg "Starte Frontend (Streamlit) auf Port ${FRONTEND_PORT} …"
mv "$LOG_DIR/frontend.log" "$LOG_DIR/frontend.log.1" 2>/dev/null || true

# Streamlit mit verbesserter Konfiguration starten
nohup streamlit run frontend/streamlit_app.py \
  --server.port "${FRONTEND_PORT}" \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false \
  > "$LOG_DIR/frontend.log" 2>&1 & 
echo $! > "$FRONTEND_PID"

echo "• Backend läuft auf:  ${BACKEND_URL}"
echo "• Frontend läuft auf: ${FRONTEND_URL}"
echo "• n8n Status:         ${BACKEND_URL}/v2/integrations/n8n/status"
echo "• Logs: ${LOG_DIR}"

# -----------------------------
# Health-Checks & Status
# -----------------------------
msg "Führe Health-Checks durch …"

# Backend Health-Check
wait_for_url "${BACKEND_URL}" 30
if curl -s -m 5 "${BACKEND_URL}/check-keys" >/dev/null 2>&1; then
  ok "Backend Health-Check: ✓"
else
  fail "Backend Health-Check: ✗"
fi

# Frontend Health-Check
wait_for_url "${FRONTEND_URL}" 30
if curl -s -m 5 "${FRONTEND_URL}" >/dev/null 2>&1; then
  ok "Frontend Health-Check: ✓"
else
  fail "Frontend Health-Check: ✗"
fi

# API-Test (optional)
msg "Teste API-Endpoints …"
if curl -s -m 5 "${BACKEND_URL}/v2/core/prompts" >/dev/null 2>&1; then
  ok "v2/core API: ✓"
else
  msg "v2/core API: Nicht verfügbar (normal bei leerer DB)"
fi

# Autopilot API-Test
if curl -s -m 5 "${BACKEND_URL}/v2/autopilot/status" >/dev/null 2>&1; then
  ok "v2/autopilot API: ✓"
else
  msg "v2/autopilot API: Nicht verfügbar (normal bei leerer DB)"
fi

# Status-Übersicht
echo ""
echo "🎯 Rico 4.0 System Status:"
echo "  Backend:  ${BACKEND_URL}"
echo "  Frontend: ${FRONTEND_URL}"
echo "  System:   ${FRONTEND_URL} → System Tab"
echo "  Autopilot: ${FRONTEND_URL} → Autopilot Tab"
echo "  Logs:     tail -f ${LOG_DIR}/backend.log"
echo "  Logs:     tail -f ${LOG_DIR}/frontend.log"
echo ""

ok "System erfolgreich gestartet! 🚀"