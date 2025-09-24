#!/bin/bash
# Rico 4.0 UI Start-Script

echo "🚀 Starte Rico 4.0 UI..."
echo "================================"

# Prüfe ob Python3 verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    exit 1
fi

# Prüfe ob Streamlit installiert ist
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit nicht installiert!"
    echo "📦 Installiere Streamlit..."
    python3 -m pip install streamlit
fi

# Prüfe ob Backend läuft
echo "🔍 Prüfe Backend-Status..."
if curl -s http://localhost:8000/check-keys >/dev/null 2>&1; then
    echo "✅ Backend läuft auf Port 8000"
else
    echo "⚠️  Backend nicht erreichbar - starte es mit: cd .. && ./start.sh"
fi

# Starte Streamlit
echo "🎯 Starte Rico 4.0 UI auf Port 8501..."
echo "🌐 Öffne: http://localhost:8501"
echo "================================"

python3 -m streamlit run streamlit_app.py --server.port 8501
