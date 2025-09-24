# Quickstart Secrets

1) .env (im Repo) enthält NUR Platzhalter.
2) .env.local (nur lokal) enthält echte Keys. Sie ist gitignored & von Cursor ausgeschlossen.
3) Start lokal:
   - Fülle .env.local mit deinen echten Keys
   - Starte System (z. B. ./stop.sh && ./start.sh oder docker compose up -d)
   - Öffne GET /check-keys → "env_source": "local", Status "OK/MISSING" je Provider
4) CI/GitHub:
   - Keys in GitHub → Settings → Secrets → Actions eintragen
   - Workflow .github/workflows/ci-verify.yml nutzt Secrets zur Verifikation
