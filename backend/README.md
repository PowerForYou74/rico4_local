# Rico Orchestrator Backend

FastAPI-basiertes Backend für das Rico Orchestrator System mit Provider-Parität und Auto-Race Logic.

## 🚀 Quick Start

```bash
# Dependencies installieren
pip install -r requirements.txt

# Environment konfigurieren
cp env.template .env.local
# Bearbeite .env.local mit deinen API-Keys

# Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API Endpoints

### Health Endpoints

- `GET /health/` - System Health Check 2.0
- `GET /health/quick` - Quick Health Check
- `GET /health/providers` - Provider Health Checks

### v1 Legacy

- `POST /v1/rico-agent` - Legacy Rico Agent Endpoint

### v2 Core

- `POST /v2/core/prompts` - Erstelle Prompt
- `GET /v2/core/prompts/{id}` - Hole Prompt
- `GET /v2/core/prompts` - Liste Prompts
- `POST /v2/core/runs` - Erstelle Run
- `GET /v2/core/runs/{id}` - Hole Run
- `GET /v2/core/runs` - Liste Runs
- `POST /v2/core/kb` - Erstelle KB Eintrag
- `GET /v2/core/kb/{id}` - Hole KB Eintrag
- `GET /v2/core/kb` - Suche KB
- `GET /v2/core/events` - Hole Events

### v2 Cashbot

- `POST /v2/cashbot/scan` - Erstelle Scan
- `GET /v2/cashbot/scans/{id}` - Hole Scan
- `GET /v2/cashbot/scans` - Liste Scans
- `GET /v2/cashbot/findings/{id}` - Hole Finding
- `GET /v2/cashbot/findings` - Liste Findings
- `POST /v2/cashbot/dispatch` - Erstelle Dispatch
- `GET /v2/cashbot/dispatches/{id}` - Hole Dispatch
- `GET /v2/cashbot/dispatches` - Liste Dispatches

### v2 Finance

- `GET /v2/finance/kpis` - Hole KPIs
- `GET /v2/finance/kpis/{id}` - Hole KPI
- `POST /v2/finance/kpis` - Erstelle KPI
- `GET /v2/finance/forecasts` - Hole Forecasts
- `GET /v2/finance/forecasts/{id}` - Hole Forecast
- `POST /v2/finance/forecasts` - Erstelle Forecast
- `GET /v2/finance/reports` - Hole Reports
- `GET /v2/finance/reports/{id}` - Hole Report
- `POST /v2/finance/reports` - Erstelle Report
- `GET /v2/finance/dashboard` - Finance Dashboard

### v2 Practice

- `POST /v2/practice/patients` - Erstelle Patient
- `GET /v2/practice/patients/{id}` - Hole Patient
- `GET /v2/practice/patients` - Liste Patienten
- `PUT /v2/practice/patients/{id}` - Update Patient
- `DELETE /v2/practice/patients/{id}` - Lösche Patient
- `POST /v2/practice/appointments` - Erstelle Termin
- `GET /v2/practice/appointments/{id}` - Hole Termin
- `GET /v2/practice/appointments` - Liste Termine
- `PUT /v2/practice/appointments/{id}` - Update Termin
- `DELETE /v2/practice/appointments/{id}` - Lösche Termin
- `POST /v2/practice/invoices` - Erstelle Rechnung
- `GET /v2/practice/invoices/{id}` - Hole Rechnung
- `GET /v2/practice/invoices` - Liste Rechnungen
- `PUT /v2/practice/invoices/{id}` - Update Rechnung
- `DELETE /v2/practice/invoices/{id}` - Lösche Rechnung
- `GET /v2/practice/dashboard` - Practice Dashboard

## 🔧 Konfiguration

### Environment Variables

```bash
# Application
APP_NAME=Rico Orchestrator
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Provider Settings
DEFAULT_PROVIDER=openai
AUTO_RACE_TIMEOUT=30.0

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key

# n8n Integration
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/rico
N8N_API_KEY=your-n8n-api-key
```

### Provider Konfiguration

Das System unterstützt drei Provider mit einheitlichem Interface:

1. **OpenAI** - GPT-3.5-turbo, GPT-4
2. **Anthropic** - Claude-3 Sonnet
3. **Perplexity** - Sonar (⚠️ Default model = "sonar")

## 🧪 Tests

```bash
# Alle Tests
pytest tests/ -v --disable-warnings

# Mit Coverage
pytest tests/ --cov=providers --cov=orchestrator --cov=api --cov=utils

# Spezifische Tests
pytest tests/test_providers.py -v
pytest tests/test_auto_race.py -v
pytest tests/test_health.py -v
pytest tests/test_cashbot.py -v
pytest tests/test_security.py -v
```

## 🏗️ Architektur

### Core Module

- **config/settings.py** - ENV Load-Order + Source-Tracking
- **utils/security.py** - Secret-Redaction Utilities
- **providers/base.py** - Provider-Interface + Error-Mapping
- **orchestrator/auto_race.py** - Auto-Race mit Task-Cancel + Tie-Breaker

### Provider Clients

- **providers/openai_client.py** - OpenAI Client
- **providers/anthropic_client.py** - Anthropic Client
- **providers/perplexity_client.py** - Perplexity Client (model="sonar")

### API Modules

- **api/health.py** - Health-Check 2.0
- **api/v1/main.py** - Legacy /rico-agent Endpoint
- **api/v2/core.py** - Prompts, Runs, KB, Events
- **api/v2/cashbot.py** - Cashbot Scan/Findings/Dispatch
- **api/v2/finance.py** - KPIs + Forecast
- **api/v2/practice.py** - Patient, Appointment, Invoice CRUD

### Integration

- **integrations/n8n_client.py** - n8n Webhook-Client

## 🔒 Sicherheit

### Secret Redaction

Das System implementiert automatische Secret-Redaction:

- Pattern-basierte Erkennung von API-Keys
- Custom Log Formatter
- Exception Handler mit Redaction
- Provider-spezifische Error-Mapping

### Test Security

- HTTP-Blocking in Tests
- Mock-basierte Provider-Tests
- Keine externen API-Calls
- Coverage-Reporting

## 📊 Monitoring

### Health Checks

- System Health: `/health/`
- Provider Status: `/health/providers`
- Quick Check: `/health/quick`

### Logging

- Secret-safe Logging
- Structured Logs
- Error Tracking

## 🚀 Deployment

### Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
docker build -t rico-backend .
docker run -p 8000:8000 rico-backend
```

## 🔄 Auto-Race Logic

Das System implementiert eine fortschrittliche Auto-Race Logic:

1. **Async Execution**: Verwendet `asyncio.wait(FIRST_COMPLETED)`
2. **Tie-Breaker**: OpenAI > Anthropic > Perplexity
3. **Timeout**: 30 Sekunden (konfigurierbar)
4. **Task Cancellation**: Automatische Cancellation von pending tasks
5. **Error Handling**: Robuste Fehlerbehandlung

## 📈 Performance

- Async/Await für bessere Performance
- Provider-Parität für optimale Auswahl
- Auto-Race für schnellste Antworten
- Health-Check für Monitoring

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details.
