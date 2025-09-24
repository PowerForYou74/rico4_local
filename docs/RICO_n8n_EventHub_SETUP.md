# Rico V5 ↔ n8n Event Hub Setup (Auto-Bootstrap)

## Übersicht

Der n8n Event Hub ist ein zentraler Orchestrierungs-Knoten zwischen Rico Backend und externen Services. Rico sendet Events an n8n, die dann automatisch verarbeitet und an verschiedene Zielsysteme (Slack, E-Mail, etc.) verteilt werden.

**🆕 Ab jetzt automatisch – keine manuellen Import-Schritte nötig!**

Das System bootstrappt sich automatisch beim Start und importiert/aktualisiert den Workflow in n8n.

## Architektur

```
Rico Backend → n8n Webhook → Event-Verarbeitung → Slack/E-Mail/APIs
```

### Event-Typen

- `daily_summary`: Täglicher Status-Report (Health, Finance, Practice KPIs)
- `cashbot.scan`: AI-basierte Cashflow-Analyse
- `cashbot.dispatch`: Automatische Weiterleitung von Findings

## Setup

### 1. Automatischer Bootstrap (Neu!)

**Keine manuellen Schritte mehr nötig!** Das System:

1. **Startet automatisch** beim Backend-Startup
2. **Importiert/aktualisiert** den Workflow in n8n
3. **Aktiviert** den Workflow automatisch
4. **Validiert** Webhook-Endpunkte

**Voraussetzungen:**
- n8n muss laufen (http://localhost:5678)
- `N8N_API_KEY` muss gesetzt sein (Personal Access Token)
- `N8N_ENABLED=true` in der .env

### 2. Environment-Variablen

Ergänze deine `.env.local` mit folgenden Variablen:

```bash
# n8n Integration
N8N_ENABLED=true
N8N_HOST=http://localhost:5678
N8N_API_KEY=changeme
N8N_TIMEOUT_SECONDS=15
N8N_WEBHOOK_BASE=${N8N_HOST}/webhook

# Backend-Base (vom Rico-Backend)
BACKEND_BASE=http://localhost:8000

# Optional: Slack (bereits vorhanden)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 3. n8n API Key Setup

**Wichtig:** Du musst einen Personal Access Token in n8n anlegen:

1. Öffne deine n8n-Instanz (http://localhost:5678)
2. Gehe zu **Settings** → **Personal Access Tokens**
3. Klicke **Create Token**
4. Gib einen Namen ein (z.B. "Rico Integration")
5. Kopiere den Token und setze ihn als `N8N_API_KEY`

**Ohne API Key funktioniert der Auto-Bootstrap nicht!**

### 4. Slack Webhook (Optional)

Falls du Slack-Nachrichten erhalten möchtest:

1. Gehe zu deinem Slack-Workspace
2. Erstelle eine neue App unter https://api.slack.com/apps
3. Aktiviere **Incoming Webhooks**
4. Erstelle einen Webhook für deinen gewünschten Channel
5. Kopiere die Webhook-URL in `SLACK_WEBHOOK_URL`

## Test-Commands

### 1. Webhook-Ping Test

```bash
curl -X POST http://localhost:5678/webhook/rico-events \
  -H "Content-Type: application/json" \
  -d '{"type":"daily_summary","data":{}}'
```

### 2. Cashbot Scan Test

```bash
curl -X POST http://localhost:5678/webhook/rico-events \
  -H "Content-Type: application/json" \
  -d '{"type":"cashbot.scan","data":{"query":"Schneller Cashflow mit AI-Services","market":"dach","online_capable":true}}'
```

### 3. Dispatch Test

```bash
curl -X POST http://localhost:5678/webhook/rico-events \
  -H "Content-Type: application/json" \
  -d '{"type":"cashbot.dispatch","data":{"finding_id":"scan_1","webhook_name":"sales-pipeline"}}'
```

### 4. Backend API Test

```bash
# Über Rico Backend API
curl -X POST http://localhost:8000/v2/core/events \
  -H "Content-Type: application/json" \
  -d '{"type":"daily_summary","data":{"test":true},"source":"manual"}'
```

## Troubleshooting

### Bootstrap-Probleme

- **401 Authentication failed**: `N8N_API_KEY` fehlt oder ist falsch
- **Connection failed**: n8n nicht erreichbar unter `N8N_HOST`
- **Workflow not found**: Bootstrap konnte Workflow nicht erstellen/aktualisieren

### Webhook-URL Probleme

- **404 Not Found**: Workflow nicht aktiviert oder falsche URL
- **403 Forbidden**: n8n-Authentifizierung erforderlich
- **429 Too Many Requests**: Rate-Limiting aktiv

### Netzwerk-Probleme

- Prüfe ob n8n unter `N8N_HOST` erreichbar ist
- Teste mit `curl` oder Browser
- Prüfe Firewall-Einstellungen

### Backend-Verbindung

- Stelle sicher, dass `BACKEND_BASE` korrekt gesetzt ist
- Rico Backend muss laufen und erreichbar sein
- Prüfe Health-Check: `GET /check-keys`

### Slack-Integration

- Webhook-URL muss gültig sein
- Slack-App muss aktiviert und berechtigt sein
- Teste Webhook direkt in Slack

### Debug-Informationen

**Bootstrap-Logs prüfen:**
```bash
tail -f logs/backend.log | grep "n8n bootstrap"
```

**n8n Status prüfen:**
```bash
curl http://localhost:8000/v2/integrations/n8n/status
```

**Manueller Bootstrap-Test:**
```bash
python integrations/n8n/bootstrap.py
```

## Workflow-Details

### Daily Summary Branch

1. **Health Check**: `GET /check-keys`
2. **Finance KPIs**: `GET /v2/finance/kpis`
3. **Practice Stats**: `GET /v2/practice/stats`
4. **Summary Builder**: Aggregiert alle Daten
5. **Slack Notification**: Sendet formatierten Report

### Cashbot Scan Branch

1. **Scan Request**: `POST /v2/cashbot/scan`
2. **Message Builder**: Formatiert Scan-Ergebnisse
3. **Slack Notification**: Sendet Scan-Status

### Cashbot Dispatch Branch

1. **Dispatch Request**: `POST /v2/cashbot/dispatch`
2. **Message Builder**: Formatiert Dispatch-Status
3. **Slack Notification**: Sendet Dispatch-Bestätigung

## Erweiterte Konfiguration

### Cron-Workflow (Optional)

Für automatische tägliche Reports:

1. Erstelle einen neuen n8n-Workflow
2. Füge **Cron**-Node hinzu (täglich 08:00)
3. Füge **HTTP Request**-Node hinzu
4. URL: `http://localhost:5678/webhook/rico-events`
5. Body: `{"type":"daily_summary","data":{}}`

### Frontend Integration (Optional)

Füge einen Quick-Action-Button im Frontend hinzu:

```javascript
const sendDailySummary = async () => {
  await fetch('/v2/core/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'daily_summary',
      data: {},
      source: 'frontend'
    })
  });
};
```

## Monitoring

### n8n Execution Logs

- Überwache Workflow-Executions in n8n
- Prüfe Fehler-Logs bei fehlgeschlagenen Runs
- Stelle sicher, dass alle Nodes erfolgreich sind

### Rico Backend Logs

```bash
# Backend-Logs prüfen
tail -f logs/backend.log | grep n8n
```

### Event-Storage

Events werden im Backend gespeichert und können abgerufen werden:

```bash
curl http://localhost:8000/v2/core/events?limit=10
```
