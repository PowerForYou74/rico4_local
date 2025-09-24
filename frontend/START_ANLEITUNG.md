# 🚀 Rico 4.0 UI - Start-Anleitung

## ✅ Status: FUNKTIONIERT!

### 🌐 Zugriff:
- **Frontend**: http://localhost:8501
- **Backend**: http://localhost:8000

## 🎯 So startest du die App:

### Option 1: Start-Script (einfach)
```bash
cd frontend
./start_ui.sh
```

### Option 2: Manuell
```bash
cd frontend
python3 -m streamlit run streamlit_app.py --server.port 8501
```

### Option 3: Mit streamlit-Befehl (falls verfügbar)
```bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

## 🔧 Falls Backend nicht läuft:
```bash
cd ..
./start.sh
```

## 🎨 Neue Features:

- **Dunkles Design** mit Smaragdgrün/Gold Theme
- **Modulare Architektur** - leicht erweiterbar
- **Health-Panel** mit Ampel-System für Provider-Status
- **Provider-Controls** mit Auto-Send-Funktion
- **Ergebnis-Tabs** mit deutschen Keys
- **n8n-Integration** (optional)
- **Debug-Modus** in der Sidebar

## 🐛 Troubleshooting:

### "streamlit: command not found"
→ Verwende: `python3 -m streamlit run streamlit_app.py`

### "File does not exist: streamlit_app.py"
→ Stelle sicher, dass du im `frontend/` Verzeichnis bist

### "Backend nicht erreichbar"
→ Starte das Backend mit `cd .. && ./start.sh`

## ✅ Test-Check:
```bash
# Teste UI-Module
python3 test_ui.py

# Prüfe Backend
curl http://localhost:8000/check-keys

# Prüfe Frontend
curl http://localhost:8501
```

## 🎉 Fertig!

Die neue modulare Rico 4.0 UI ist einsatzbereit! 🐾✨
