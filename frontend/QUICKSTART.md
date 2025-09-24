# Rico 4.0 UI - Quickstart

## 🚀 Sofort starten

### Option 1: Start-Script (empfohlen)
```bash
cd frontend
./start_ui.sh
```

### Option 2: Manuell
```bash
cd frontend
python3 -m streamlit run streamlit_app.py --server.port 8501
```

### Option 3: Mit streamlit-Befehl (falls im PATH)
```bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

## 🌐 Zugriff

- **Frontend**: http://localhost:8501
- **Backend**: http://localhost:8000
- **API-Docs**: http://localhost:8000/api/v1/docs

## 🔧 Backend starten

Falls das Backend nicht läuft:
```bash
cd ..
./start.sh
```

## 🎯 Features der neuen UI

- **Dunkles Design** mit Smaragdgrün/Gold Theme
- **Modulare Architektur** - leicht erweiterbar
- **Health-Panel** mit Ampel-System
- **Provider-Controls** mit Auto-Send
- **Ergebnis-Tabs** mit deutschen Keys
- **n8n-Integration** (optional)
- **Debug-Modus** in der Sidebar

## 🐛 Troubleshooting

### "streamlit: command not found"
```bash
python3 -m streamlit run streamlit_app.py
```

### "Backend nicht erreichbar"
```bash
cd ..
./start.sh
```

### "Import-Fehler"
```bash
cd frontend
python3 test_ui.py
```

## 📁 Dateistruktur

```
frontend/
├── streamlit_app.py          # Neue modulare App
├── streamlit_app_backup.py   # Backup der alten App
├── start_ui.sh              # Start-Script
├── test_ui.py               # Test-Suite
├── ui/                      # UI-Module
│   ├── theme.py             # Design-System
│   ├── layout.py            # Layout-Komponenten
│   └── sections/            # UI-Sektionen
└── integrations/            # n8n-Integration
```

## ✅ Status-Check

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
