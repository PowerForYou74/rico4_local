# Rico V5 n8n Workflows

## Import-Anleitung

1. **n8n starten**: `n8n start`
2. **Workflow importieren**: 
   - n8n → Create Workflow → Menü ⋮ → Import from file
   - Dateien wählen:
     - `integrations/n8n/workflows/rico_v5_event_hub.json`
     - `integrations/n8n/workflows/rico_v5_autopilot.json`

## Vorbedingungen

- **Backend läuft lokal** auf `http://localhost:8000`
- **Environment Variables** in n8n setzen:
  - `BACKEND_BASE=http://localhost:8000`
  - `SLACK_WEBHOOK_URL=<your-webhook-url>` (optional)

## Workflows

### 1. Rico V5 Event Hub
- **Webhook**: `/webhook/rico-events`
- **Events**: `daily_summary`, `cashbot.scan`, `cashbot.dispatch`
- **APIs**: Health, Finance KPIs, Practice Stats, Cashbot

### 2. Rico V5 Autopilot
- **Hourly**: Metrics rollup
- **Daily**: Experiments evaluation + KB ingest
- **Weekly**: Prompt review

## API-Tests (manuell)

```bash
# Hourly Metrics
curl -X POST http://localhost:8000/v2/autopilot/metrics/rollup

# Daily Evaluation
curl -X POST http://localhost:8000/v2/autopilot/evaluate

# Weekly Prompt Review
curl -X POST http://localhost:8000/v2/autopilot/kb/ingest \
  -H "Content-Type: application/json" \
  -d '{"docs_path": "docs", "results_path": "data/results"}'

# KB Ingest
curl -X POST http://localhost:8000/v2/autopilot/kb/ingest \
  -H "Content-Type: application/json" \
  -d '{"docs_path": "docs", "results_path": "data/results"}'
```

## Hinweise

- **Slack-Nodes**: Vorerst disabled (Credentials erst in n8n setzen, dann aktivieren)
- **Absolute URLs**: Alle HTTP-Requests verwenden `http://localhost:8000`
- **Version**: `v5-fixed-abs-urls`
- **n8n v1.x kompatibel**: Keine experimentellen Properties

## Troubleshooting

- **Import-Fehler**: Prüfe JSON-Syntax, entferne unbekannte Properties
- **Connection-Fehler**: Backend muss laufen, URLs prüfen
- **Slack-Fehler**: `SLACK_WEBHOOK_URL` setzen oder Nodes deaktivieren
