#!/bin/bash
# Rico 4.0 Starter Script

BACKEND_PORT=8000
FRONTEND_PORT=8501
BACKEND_LOG=logs/backend.log
FRONTEND_LOG=logs/frontend.log

echo "=== Rico 4.0 Starter ==="

# Logs-Verzeichnis anlegen
mkdir -p logs

# Falls alte Prozesse laufen → killen
echo "• Beende alte Prozesse (falls vorhanden) …"
kill $(lsof -t -i:${BACKEND_PORT}) 2>/dev/null
kill $(lsof -t -i:${FRONTEND_PORT}) 2>/dev/null

# ----------------------------
# Backend starten (Uvicorn)
# ----------------------------
echo "• Starte Backend (Uvicorn) auf Port ${BACKEND_PORT} …"
cd backend
uvicorn app.main:app --reload --port "${BACKEND_PORT}" >"../${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!
cd ..

sleep 3

# ----------------------------
# Frontend starten (Streamlit)
# ----------------------------
echo "• Starte Frontend (Streamlit) auf Port ${FRONTEND_PORT} …"
cd frontend
streamlit run streamlit_app.py --server.port="${FRONTEND_PORT}" >"../${FRONTEND_LOG}" 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 3

echo "=========================================="
echo " Backend läuft auf:   http://127.0.0.1:${BACKEND_PORT}"
echo " Frontend läuft auf:  http://127.0.0.1:${FRONTEND_PORT}"
echo " Logs unter:          ./logs/"
echo "=========================================="
echo "Zum Beenden: kill ${BACKEND_PID} ${FRONTEND_PID}"