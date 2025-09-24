# Rico Orchestrator System

Ein fortschrittliches AI Provider Orchestration System mit Auto-Race Logic, entwickelt mit FastAPI (Python) und Next.js 14 (TypeScript).

## 🚀 Features

- **Provider-Parität**: OpenAI, Anthropic, Perplexity mit einheitlichem Response-Schema
- **Auto-Race Logic**: Async `asyncio.wait(FIRST_COMPLETED)` mit deterministischem Tie-Breaker
- **Health-Check 2.0**: Schema `{status, latency_ms, model, env_source}`
- **v2 Endpoints**: Core, Practice, Finance, Cashbot
- **Secret-Redaction**: Logging/Exception-Handler mit Key/Token-Masking
- **Next.js Frontend**: App Router + Zustand + shadcn/ui Components
- **Mock-Tests**: Vollständig, keine Real-HTTP Calls
- **n8n Integration**: Webhook-Client mit ENV-based Config
- **CI-Security**: HTTP-Blocking in Tests

## 📋 Voraussetzungen

- Python 3.11+
- Node.js 18+
- npm oder yarn

## 🛠️ Installation

### Backend Setup

```bash
# Backend Dependencies installieren
cd backend
pip install -r requirements.txt

# Environment konfigurieren
cp env.template .env.local
# Bearbeite .env.local mit deinen API-Keys
```

### Frontend Setup

```bash
# Frontend Dependencies installieren
cd frontend
npm install

# Environment konfigurieren
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

## 🚀 Starten

### Lokale Entwicklung mit Docker

```bash
# Alle Services starten
docker compose up -d

# Mit n8n (optional)
docker compose --profile n8n up -d

# Mit Nginx Proxy (optional)
docker compose --profile proxy up -d

# Logs anzeigen
docker compose logs -f

# Services stoppen
docker compose down
```

### Backend starten

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend starten

```bash
cd frontend
npm run dev
```

### Beide gleichzeitig

```bash
# Im Root-Verzeichnis
./start.sh
```

## 🧪 Tests ausführen

### Backend Tests

```bash
cd backend
pytest tests/ -v --disable-warnings

# Mit Coverage
pytest tests/ --cov=providers --cov=orchestrator --cov=api --cov=utils
```

### Frontend Tests

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

## 📚 API Dokumentation

### Health Endpoints

- `GET /health/` - System Health Check 2.0
- `GET /health/quick` - Quick Health Check
- `GET /health/providers` - Provider-spezifische Health Checks

### v2 Core Endpoints

- `POST /v2/core/prompts` - Erstelle Prompt mit Auto-Race
- `GET /v2/core/prompts/{id}` - Hole spezifischen Prompt
- `POST /v2/core/runs` - Erstelle Run mit mehreren Prompts
- `POST /v2/core/kb` - Erstelle Knowledge Base Eintrag
- `GET /v2/core/kb` - Suche Knowledge Base

### v2 Cashbot Endpoints

- `POST /v2/cashbot/scan` - Erstelle Cashbot Scan
- `GET /v2/cashbot/scans/{id}` - Hole Scan-Ergebnisse
- `POST /v2/cashbot/dispatch` - Erstelle Dispatch

### v2 Finance Endpoints

- `GET /v2/finance/kpis` - Hole KPIs
- `GET /v2/finance/forecasts` - Hole Forecasts
- `GET /v2/finance/dashboard` - Finance Dashboard

### v2 Practice Endpoints

- `GET /v2/practice/dashboard` - Practice Dashboard
- `POST /v2/practice/patients` - Erstelle Patient
- `POST /v2/practice/appointments` - Erstelle Termin
- `POST /v2/practice/invoices` - Erstelle Rechnung

## 🔧 Konfiguration

### Environment Variables

```bash
# Backend (.env.local)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/rico
N8N_API_KEY=your-n8n-api-key

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Provider Konfiguration

Das System unterstützt drei Provider:

1. **OpenAI** - GPT-3.5-turbo, GPT-4
2. **Anthropic** - Claude-3 Sonnet
3. **Perplexity** - Sonar (⚠️ Default model = "sonar")

### Auto-Race Logic

- Verwendet `asyncio.wait(FIRST_COMPLETED)`
- Tie-Breaker: OpenAI > Anthropic > Perplexity
- Timeout: 30 Sekunden (konfigurierbar)

## 🏗️ Architektur

### Backend Struktur

```
backend/
├── config/
│   └── settings.py          # ENV Load-Order + Source-Tracking
├── utils/
│   └── security.py         # Secret-Redaction Utilities
├── providers/
│   ├── base.py             # Provider-Interface + Error-Mapping
│   ├── openai_client.py    # OpenAI Client
│   ├── anthropic_client.py # Anthropic Client
│   └── perplexity_client.py # Perplexity Client (model="sonar")
├── orchestrator/
│   └── auto_race.py        # Auto-Race mit Task-Cancel + Tie-Breaker
├── api/
│   ├── health.py           # Health-Check 2.0
│   ├── v1/
│   │   └── main.py         # Legacy /rico-agent Endpoint
│   └── v2/
│       ├── core.py         # Prompts, Runs, KB, Events
│       ├── cashbot.py      # Cashbot Scan/Findings/Dispatch
│       ├── finance.py      # KPIs + Forecast
│       └── practice.py     # Patient, Appointment, Invoice CRUD
├── integrations/
│   └── n8n_client.py       # n8n Webhook-Client
└── tests/                  # Mock-basierte Tests
```

### Frontend Struktur

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root Layout
│   │   ├── page.tsx        # Dashboard
│   │   └── agents/
│   │       └── page.tsx    # Agent Workflow
│   ├── components/
│   │   └── ui/             # shadcn/ui Components
│   ├── lib/
│   │   └── api.ts          # API Client
│   └── store/
│       └── app-store.ts    # Zustand Global Store
└── package.json
```

## 🔒 Sicherheit

### Secret Redaction

- Automatische Redaktion von API-Keys in Logs
- Pattern-basierte Erkennung von Secrets
- Custom Log Formatter
- Exception Handler mit Redaction

### CI/CD Security

- HTTP-Blocking in Tests
- Keine externen API-Calls in Tests
- Mock-basierte Provider-Tests
- Coverage-Reporting

## 🚀 Deployment

### Docker (Optional)

```bash
# Backend
cd backend
docker build -t rico-backend .

# Frontend
cd frontend
docker build -t rico-frontend .
```

### Production

```bash
# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm run build
npm start
```

## 📊 Monitoring

### Health Checks

- System Health: `/health/`
- Provider Status: `/health/providers`
- Quick Check: `/health/quick`

### Logging

- Secret-safe Logging
- Structured Logs
- Error Tracking

## 🚀 Deploy (CI/CD)

### Server-Bootstrap (einmalig)

```bash
# Auf dem Server ausführen
curl -fsSL https://raw.githubusercontent.com/your-repo/main/deploy/server_bootstrap.sh | bash

# Oder manuell
wget https://raw.githubusercontent.com/your-repo/main/deploy/server_bootstrap.sh
chmod +x server_bootstrap.sh
./server_bootstrap.sh
```

### GitHub Secrets konfigurieren

In den Repository Settings → Secrets and variables → Actions:

- `SSH_HOST`: IP-Adresse oder Domain des Servers
- `SSH_USER`: Benutzername für SSH (z.B. `ubuntu`, `root`)
- `SSH_KEY`: Privater SSH-Schlüssel für Server-Zugriff

### Automatisches Deploy

Nach jedem Push auf `main` Branch wird automatisch deployed:

1. **GitHub Action** startet
2. **SSH-Verbindung** zum Server
3. **Git Pull** der neuesten Änderungen
4. **Docker Images** werden aktualisiert
5. **Services** werden neu gestartet
6. **Health Check** wird durchgeführt

### Manuelles Deploy

```bash
# Auf dem Server
cd /opt/rico4
git pull origin main
bash deploy/deploy.sh
```

### Service-URLs

Nach erfolgreichem Deploy:

- **Backend API**: `http://your-server:8000`
- **Frontend**: `http://your-server:3000`
- **n8n** (optional): `http://your-server:5678`
- **Nginx Proxy** (optional): `http://your-server:80`

### Troubleshooting

```bash
# Service Status prüfen
docker compose ps

# Logs anzeigen
docker compose logs -f

# Health Check
curl http://localhost:8000/health/quick

# Services neu starten
docker compose restart
```

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details.

## 🆘 Support

Bei Fragen oder Problemen:

1. Überprüfe die Dokumentation
2. Schaue in die Issues
3. Erstelle ein neues Issue

## 🔄 Changelog

### v2.0.0
- Vollständige Neuentwicklung
- Auto-Race Logic implementiert
- Provider-Parität erreicht
- Next.js 14 Frontend
- Comprehensive Testing
- CI/CD Pipeline