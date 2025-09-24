# Rico V5 System - Vollständiges CI/CD & Deploy-System

Ein produktionsreifes AI Provider Orchestration System mit FastAPI (Backend), Next.js 14 (Frontend) und n8n (Workflows), vollständig containerisiert und mit automatischem Deployment.

## 🚀 Features

- **Vollständig containerisiert**: Docker Compose mit Health-Checks
- **Reverse Proxy**: Nginx mit Routing und Security-Headers
- **CI/CD Pipeline**: GitHub Actions mit automatischem Deploy
- **Health-Monitoring**: JSON-Logging und Service-Health-Checks
- **Provider-Parität**: OpenAI, Anthropic, Perplexity
- **n8n Integration**: Workflow-Automatisierung
- **Production-Ready**: Idempotente Deploy-Skripte

## 🏗️ Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx:80      │    │   Frontend:3000 │    │   Backend:8000  │
│   (Reverse     │    │   (Next.js 14)   │    │   (FastAPI)     │
│    Proxy)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   n8n:5678      │
                    │   (Workflows)   │
                    └─────────────────┘
```

## 🚀 Quick Start

### Lokale Entwicklung

```bash
# 1. Environment konfigurieren
cp env.template .env.local
# Bearbeite .env.local mit deinen API-Keys

# 2. Alle Services starten
docker compose up -d

# 3. Services testen
curl http://localhost:8000/health    # Backend
curl http://localhost:3000/api/health  # Frontend
curl http://localhost/health         # Nginx
```

### Server-Deploy

```bash
# 1. Server vorbereiten
ssh user@server "bash <(curl -s https://raw.githubusercontent.com/your-repo/main/deploy/server_bootstrap.sh)"

# 2. Code synchronisieren
rsync -avz --delete -e "ssh" ./ user@server:/opt/rico4/

# 3. Deploy ausführen
ssh user@server "cd /opt/rico4 && bash deploy/deploy.sh"
```

## 🔧 Konfiguration

### Environment-Variablen

Kopiere `env.template` zu `.env.local` und setze deine Werte:

```bash
# API Keys (erforderlich)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PPLX_API_KEY=pplx-your-perplexity-key

# Service-Konfiguration
N8N_ENABLED=true
DEBUG=false
```

### GitHub Actions Secrets

Konfiguriere diese Secrets in deinem GitHub Repository:

- `SSH_HOST`: Server-IP-Adresse
- `SSH_USER`: SSH-Benutzername
- `SSH_KEY`: SSH-Private-Key
- `SSH_PORT`: SSH-Port (optional, Standard: 22)

## 🌐 Service-URLs

- **Hauptzugang**: http://localhost (Nginx)
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **n8n**: http://localhost:5678

## 🔍 Health-Checks

```bash
# Backend
curl http://localhost:8000/health
# → {"status":"ok","service":"backend"}

# Frontend
curl http://localhost:3000/api/health
# → {"status":"ok","service":"frontend"}

# Nginx
curl http://localhost/health
# → "healthy"
```

## 🚀 Deploy-Ablauf

### Automatisch (GitHub Actions)

1. Push auf `main` Branch
2. GitHub Actions führt Build und Deploy aus
3. Health-Checks werden automatisch durchgeführt

### Manuell

```bash
# 1. Code pushen
git push origin main

# 2. Auf Server deployen
ssh user@server "cd /opt/rico4 && git pull && bash deploy/deploy.sh"
```

## 📊 Monitoring

### Container-Status

```bash
docker compose ps
```

### Logs anzeigen

```bash
# Alle Services
docker compose logs

# Einzelne Services
docker compose logs backend
docker compose logs frontend
docker compose logs n8n
docker compose logs nginx
```

### Health-Checks

```bash
# Alle Services prüfen
curl -f http://localhost:8000/health && \
curl -f http://localhost:3000/api/health && \
curl -f http://localhost/health && \
echo "✅ Alle Services sind gesund"
```

## 🛠️ Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker compose logs [service-name]

# Container neu starten
docker compose restart [service-name]

# Alle Container neu starten
docker compose down && docker compose up -d
```

### Health-Check fehlgeschlagen

```bash
# Service-spezifische Logs
docker compose logs [service-name]

# Container-Status prüfen
docker compose ps

# Health-Check manuell testen
curl -v http://localhost:[port]/health
```

### n8n Probleme

```bash
# n8n Daten zurücksetzen
docker compose down
rm -rf n8n_data/
docker compose up -d n8n
```

## 📁 Projektstruktur

```
rico4_local/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   └── main.py         # Hauptanwendung
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   └── api/health/ # Health-Route
│   │   └── components/
│   ├── Dockerfile
│   └── package.json
├── deploy/                  # Deploy-Skripte
│   ├── server_bootstrap.sh
│   ├── deploy.sh
│   └── nginx/
│       └── nginx.conf
├── .github/workflows/       # CI/CD
│   └── deploy.yml
├── docker-compose.yml       # Container-Orchestrierung
├── env.template             # Environment-Template
└── README.md               # Diese Datei
```

## 🔒 Sicherheit

- **Keine Secrets im Repository**
- **SSH-Key-basierte Authentifizierung**
- **Security-Headers in Nginx**
- **Rate Limiting aktiviert**
- **Container als Non-Root-User**

## 📈 Performance

- **Multi-Stage Docker Builds**
- **Gzip-Kompression**
- **Health-Check-basierte Dependencies**
- **JSON-Structured Logging**
- **Container-Health-Monitoring**

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

MIT License - siehe LICENSE-Datei für Details.

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