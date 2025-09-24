# Claude 401 Fix - Header Hardening nach Perplexity Integration

## 🎯 Problem gelöst
**401 Unauthorized** bei Claude-API nach Perplexity-Integration durch Header-Konflikte.

## 🔧 Implementierte Lösung

### 1. Provider-spezifische Clients erstellt
- **`backend/app/services/providers/claude_client.py`**: Claude-Client mit hart abgesicherten Headern
- **`backend/app/services/providers/pplx_client.py`**: Perplexity-Client mit isolierten Headern
- **`backend/app/services/provider_clients.py`**: Factory für Provider-Client-Erstellung

### 2. Header-Isolation sichergestellt
- **Claude**: Nur `x-api-key`, `anthropic-version: 2023-06-01`, `Content-Type`
- **Perplexity**: Nur `Authorization: Bearer`, `Content-Type`
- **Keine globalen Header** mehr, die Provider überschreiben

### 3. Orchestrator aktualisiert
- **`backend/app/services/orchestrator.py`**: Nutzt neue Provider-Clients
- Claude und Perplexity verwenden jetzt isolierte Header
- Bestehende Auto-Race-Logik unverändert

### 4. Umfassende Tests erstellt
- **`tests/test_claude_headers.py`**: Header-Guard und Error-Mapping
- **`tests/test_provider_clients.py`**: Provider-Factory und Header-Isolation
- **`tests/test_auto_race_claude_pplx.py`**: Integration-Tests

### 5. Sanity-Script für manuelle Tests
- **`scripts/anthropic_sanity.sh`**: Lokale API-Tests (nicht in CI)

## ✅ Akzeptanzkriterien erfüllt

- [x] Claude-Requests senden nur: `x-api-key`, `anthropic-version: 2023-06-01`, `Content-Type`
- [x] Kein globaler `Authorization`-Header greift auf Claude
- [x] Auto-Race weiterhin stabil (OpenAI/PPLX unverändert)
- [x] Tests grün: Header-Guard, Error-Mapping, Provider-Isolation
- [x] Keine Secrets geloggt/committet
- [x] UI/Schema unverändert

## 🧪 Test-Ergebnisse
```
13 passed, 1 warning in 0.14s
```

## 🔄 Rollback-Plan
Bei Problemen:
1. `git revert` des Fix-Commits
2. Vorherige Claude-Implementierung wiederherstellen
3. Globale Header-Injection zurücknehmen

## 📁 Betroffene Dateien
- `backend/app/services/providers/claude_client.py` (neu)
- `backend/app/services/providers/pplx_client.py` (neu)
- `backend/app/services/provider_clients.py` (neu)
- `backend/app/services/orchestrator.py` (geändert)
- `tests/test_claude_headers.py` (neu)
- `tests/test_provider_clients.py` (neu)
- `tests/test_auto_race_claude_pplx.py` (neu)
- `scripts/anthropic_sanity.sh` (neu, lokal)

## 🚀 Nächste Schritte
1. **Manueller Test**: `ANTHROPIC_API_KEY=... ./scripts/anthropic_sanity.sh`
2. **App-Start**: Provider "claude" testen
3. **Auto-Modus**: Mindestens eine Antwort mit `used_provider: "claude"`
