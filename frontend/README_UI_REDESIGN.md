# Rico 4.0 UI-Redesign - Modulare Architektur

## 🎯 Übersicht

Das Rico 4.0 Frontend wurde komplett überarbeitet mit einer modularen Architektur, dunklem Design und optionaler n8n-Integration.

## 📁 Neue Dateistruktur

```
frontend/
├── streamlit_app.py              # Neue modulare Haupt-App
├── streamlit_app_backup.py       # Backup der ursprünglichen App
├── ui/
│   ├── __init__.py
│   ├── theme.py                  # Design-System (Smaragdgrün/Gold)
│   ├── layout.py                 # Layout-Komponenten (Header, Sidebar)
│   └── sections/
│       ├── __init__.py
│       ├── health_panel.py       # Health-Check mit Ampel-System
│       ├── provider_controls.py  # Request-Composer
│       ├── result_tabs.py        # Ergebnis-Darstellung
│       ├── n8n_panel.py          # n8n-Integration (optional)
│       └── toast.py              # Notification-System
└── integrations/
    ├── __init__.py
    ├── n8n_client.py             # n8n Webhook-Client
    └── n8n_webhooks.local.json   # n8n Webhook-Konfiguration
```

## 🎨 Design-System

### Farben
- **Hintergrund**: Dunkel (`#0f1216`)
- **Brand**: Smaragdgrün (`#009688`)
- **Akzent**: Gold (`#D4AF37`)
- **Status**: Grün/Gelb/Rot für Ampel-System

### Komponenten
- **Header**: Mit Backend-Status-Anzeige
- **Sidebar**: Modulare Panels
- **Status-Chips**: Farbkodierte Status-Anzeige
- **Info-Cards**: Strukturierte Information

## 🔧 Session State Management

Konsistente Session State Keys:
```python
SS_KEYS = {
    'ss_input_text': '',
    'ss_provider': 'auto', 
    'ss_task_type': 'analyse',
    'ss_last_result': None,
    'ss_last_meta': None,
    'ss_auto_send_triggered': False,
    'ss_backend_reachable': True
}
```

## 🚦 Health-Panel

- **Ampel-System**: Visueller Status aller Provider
- **Latenz-Anzeige**: Response-Zeit in ms
- **Auto-Refresh**: Automatische Aktualisierung
- **Offline-Handling**: Graceful Degradation

## 📝 Provider-Controls

- **Request-Composer**: Strukturierte Eingabe
- **Provider-Auswahl**: Auto/OpenAI/Claude/Perplexity
- **Task-Typ**: Analyse/Recherche/Strategie/Code
- **Auto-Send**: Automatisches Senden bei Eingabe

## 📊 Ergebnis-Tabs

Deutsche Keys für bessere UX:
- **Zusammenfassung**: `kurz_zusammenfassung`
- **Kernbefunde**: `kernbefunde`
- **Action Plan**: `action_plan`
- **Risiken**: `risiken`
- **Cashflow-Radar**: `cashflow_radar`
- **Team-Rollen**: `team_rolle`
- **Orchestrator-Log**: `orchestrator_log`
- **Rohdaten**: JSON-Download

## 🔗 n8n-Integration (Optional)

### Aktivierung
```bash
# In .env setzen
N8N_ENABLED=true
N8N_WEBHOOKS_FILE=integrations/n8n_webhooks.local.json
```

### Webhook-Konfiguration
```json
[
  {
    "name": "rico_analysis_webhook",
    "url": "http://localhost:5678/webhook/rico-analysis",
    "description": "Webhook für Rico-Analysen"
  }
]
```

### Features
- **Webhook-Test**: Test von n8n Webhooks
- **Rico-Ergebnis senden**: Automatisches Senden von Ergebnissen
- **Payload-Vorschau**: JSON-Struktur anzeigen
- **Latenz-Messung**: Response-Zeit der Webhooks

## 🚀 Verwendung

### Starten der App
```bash
cd frontend
streamlit run streamlit_app.py
```

### Debug-Modus
- Sidebar: "🔧 Debug-Modus" aktivieren
- Zeigt Session State, Backend-Status, cURL-Commands

### Beispiel-Buttons
- **Cashflow-Idee analysieren**: Vordefinierter Prompt
- **Quartalsfokus vorschlagen**: Business-Planning
- **Risiken & Maßnahmen**: Risk-Assessment

## 🔄 Migration von alter App

1. **Backup erstellt**: `streamlit_app_backup.py`
2. **Session State**: Konsistente Keys beibehalten
3. **API-Kompatibilität**: Keine Breaking Changes
4. **Theme**: Dunkles Design aktiviert

## 🛠️ Entwicklung

### Neue Komponenten hinzufügen
1. Erstelle Datei in `ui/sections/`
2. Importiere in `streamlit_app.py`
3. Füge zu Sidebar oder Main-Content hinzu

### Theme anpassen
- Bearbeite `ui/theme.py`
- CSS-Variablen in `inject_theme()`
- Farben in `TOKENS['colors']`

### n8n erweitern
- Neue Webhooks in `n8n_webhooks.local.json`
- Client-Logic in `integrations/n8n_client.py`
- UI in `ui/sections/n8n_panel.py`

## 📋 TODO

- [ ] Keyboard-Shortcuts (Cmd/Ctrl + Enter)
- [ ] Dark/Light Mode Toggle
- [ ] Export-Funktionen erweitern
- [ ] Mobile-Responsive Optimierung
- [ ] Performance-Monitoring
- [ ] Error-Boundary Components

## 🎉 Erfolg!

Das Rico 4.0 Frontend ist jetzt vollständig modular, modern und erweiterbar!
