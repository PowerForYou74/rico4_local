#!/bin/bash
echo "⛔ Rico 4.0 stoppen..."

# Alle Prozesse von uvicorn und streamlit beenden
pkill -f "uvicorn app.main:app"
pkill -f "streamlit run streamlit_app.py"

echo "✅ Backend & Frontend gestoppt."