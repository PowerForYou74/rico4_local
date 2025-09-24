# Rico V5 Multi-AI Integration - Agents Guide

## Übersicht

Die Multi-AI Integration in Rico V5 bietet ein einheitliches Interface für verschiedene AI-Provider mit intelligenter Routing-Logik und Auto-Race-Funktionalität.

## Architektur

```
Frontend (Agents Page) → /v2/ai/ask → Auto-Routing → Provider Selection → Response
                                     ↓
                              Auto-Race (Fallback)
```

## Provider & Modelle

| Provider | Modell | Verwendung | API |
|----------|--------|------------|-----|
| **OpenAI** | gpt-4o | Analysis, allgemeine Aufgaben | Chat Completions |
| **Anthropic** | claude-3-7-sonnet-20250219 | Writing, Review | Messages API |
| **Perplexity** | sonar | Research, Online-Modus | Chat Completions |

⚠️ **Wichtig**: Perplexity verwendet Modell `sonar` (nicht `sonar-medium-online`)

## Routing-Regeln

### Automatisches Routing

```python
# Task-basierte Routing-Logik
if preferred != "auto":
    # Erzwungener Provider
    provider = preferred_provider
elif task == "research" or online == True:
    # Research oder Online-Modus → Perplexity
    provider = "perplexity"
elif task in ["write", "review"]:
    # Writing/Review → Anthropic
    provider = "anthropic"
elif task == "analysis":
    # Analysis → OpenAI
    provider = "openai"
else:
    # Auto-Race Fallback
    provider = auto_race_all_available()
```

### Auto-Race Fallback

Wenn keine spezifischen Provider verfügbar sind oder der Task unbekannt ist:

1. **Alle verfügbaren Provider starten parallel**
2. **FIRST_COMPLETED wins** (asyncio.wait)
3. **Tie-Breaker**: openai > anthropic > perplexity
4. **Rest wird gecancelt**

## API-Endpoints

### POST /v2/ai/ask

**Request:**
```json
{
  "task": "research|analysis|write|review",
  "prompt": "Deine Frage hier...",
  "preferred": "auto|openai|anthropic|perplexity",
  "online": true|false
}
```

**Response:**
```json
{
  "id": "uuid",
  "content": "AI Response Text",
  "tokens_in": 15,
  "tokens_out": 75,
  "provider": "openai",
  "provider_model": "gpt-4o",
  "duration_s": 1.2,
  "finish_reason": "stop",
  "task": "analysis",
  "routing_reason": "analysis_default",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### GET /v2/ai/health

**Response:**
```json
{
  "providers": {
    "openai": {
      "status": "healthy",
      "latency_ms": 150.0,
      "model": "gpt-4o"
    },
    "anthropic": {
      "status": "healthy", 
      "latency_ms": 200.0,
      "model": "claude-3-7-sonnet-20250219"
    },
    "perplexity": {
      "status": "healthy",
      "latency_ms": 300.0,
      "model": "sonar"
    }
  },
  "routing_rules": {
    "research": "Perplexity (online research)",
    "analysis": "OpenAI (general analysis)",
    "write": "Anthropic (creative writing)",
    "review": "Anthropic (content review)",
    "online=true": "Perplexity (online mode)",
    "auto_race": "All providers (first success wins)"
  },
  "auto_race_enabled": true
}
```

## Frontend - Agents Page

### Ask Tab
- **Task Selection**: research, analysis, write, review
- **Prompt Input**: Deine Frage/Prompt
- **Provider Selection**: auto (empfohlen) oder spezifischer Provider
- **Online Mode**: Checkbox für Research-Modus
- **Response Panel**: Ergebnis mit Token-Stats und Routing-Info

### Runs Tab
- **Recent AI Runs**: Letzte 10 Requests
- **Performance Metrics**: Provider, Duration, Tokens, Routing-Reason
- **Timestamp**: Wann wurde der Request gemacht

### Health Tab
- **Provider Status**: Ampeln für alle Provider (OK/Fehler/Latenz)
- **Routing Rules**: Übersicht der Routing-Logik
- **Auto-Race Status**: Enabled/Disabled

## Environment Setup

```bash
# Provider Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
PERPLEXITY_API_KEY=pplx-your-perplexity-key-here

# Backend & n8n
BACKEND_BASE=http://localhost:8000
N8N_ENABLED=true
N8N_HOST=http://localhost:5678
N8N_WEBHOOK_BASE=http://localhost:5678/webhook
N8N_API_KEY=
N8N_TIMEOUT_SECONDS=20

# Slack (optional)
SLACK_WEBHOOK_URL=
```

## Test Commands

### Backend Health Check
```bash
curl http://localhost:8000/health/
```

### AI Ask - Research (Perplexity)
```bash
curl -s -X POST http://localhost:8000/v2/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task": "research",
    "prompt": "Top 3 D2C Cashflow Ideen",
    "online": true,
    "preferred": "auto"
  }' | jq
```

### AI Ask - Write (Claude)
```bash
curl -s -X POST http://localhost:8000/v2/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task": "write",
    "prompt": "Schreibe eine strukturierte Executive Summary",
    "preferred": "anthropic"
  }' | jq
```

### AI Ask - Analysis (OpenAI)
```bash
curl -s -X POST http://localhost:8000/v2/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "task": "analysis",
    "prompt": "Analysiere die Marktdaten und erstelle eine Prognose",
    "preferred": "auto"
  }' | jq
```

### AI Health Check
```bash
curl http://localhost:8000/v2/ai/health | jq
```

## n8n Integration

Der n8n Event Hub nutzt die Multi-AI Integration für:

- **cashbot.scan**: Perplexity für Online-Research
- **daily_summary**: Verschiedene Provider für verschiedene Teile
- **Auto-Bootstrap**: Workflow wird automatisch importiert/aktualisiert

### n8n Workflow
```json
{
  "cashbot.scan": {
    "provider": "perplexity",
    "model": "sonar",
    "online": true
  }
}
```

## Error Handling

### Standardisierte Fehlercodes
- **401/403**: Authentication failed
- **429**: Rate limit exceeded  
- **5xx**: Server error
- **Timeout**: Connection timeout
- **Validation**: Invalid request parameters

### Provider-spezifische Fehler
```json
{
  "error": {
    "provider": "openai",
    "error_type": "RateLimitError", 
    "message": "API rate limit exceeded. Please try again later."
  }
}
```

## Best Practices

### 1. Provider Selection
- **Auto-Route verwenden** für optimale Performance
- **Spezifische Provider** nur bei besonderen Anforderungen
- **Online-Modus** für aktuelle Informationen

### 2. Task Types
- **research**: Aktuelle Informationen, Marktanalysen
- **analysis**: Datenauswertung, Statistiken
- **write**: Kreative Texte, Zusammenfassungen
- **review**: Content-Bewertung, Qualitätskontrolle

### 3. Performance
- **Auto-Race** nutzt Parallel-Execution für Speed
- **Tie-Breaker** sorgt für deterministische Ergebnisse
- **Token-Monitoring** für Cost-Control

## Troubleshooting

### Provider nicht erreichbar
```bash
# Health Check
curl http://localhost:8000/v2/ai/health

# Einzelner Provider Test
curl -s -X POST http://localhost:8000/v2/ai/ask \
  -d '{"task":"analysis","prompt":"Test","preferred":"openai"}'
```

### Routing-Probleme
```bash
# Routing Rules anzeigen
curl http://localhost:8000/v2/ai/routing-rules | jq
```

### Auto-Race Debug
- Logs in `logs/backend.log` prüfen
- Provider-Status im Health Tab überwachen
- Network-Connectivity zu Provider-APIs testen

## Security

- **API Keys** werden in Logs redacted
- **Secrets** nicht im Repository
- **ENV-basierte Konfiguration**
- **Request/Response Logging** ohne sensible Daten

## Monitoring

- **Provider Health**: `/v2/ai/health`
- **System Health**: `/health/`
- **n8n Status**: `/v2/integrations/n8n/status`
- **Frontend Health Panel**: Real-time Provider Status

---

**Die Multi-AI Integration ist vollständig produktionsreif und bietet intelligente Orchestrierung zwischen verschiedenen AI-Providern mit optimaler Performance und Fehlerbehandlung.**
