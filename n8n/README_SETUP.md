# n8n Setup (macOS, Docker)
1) Docker Desktop starten.
2) In `.env` das Passwort **N8N_BASIC_AUTH_PASSWORD** unbedingt ändern.
3) Start:
   - cd ~/Projects/rico4_local/n8n
   - docker compose pull
   - docker compose up -d
4) Öffnen: http://localhost:5678  (Login lt. .env)
5) Autostart (optional):
   - mkdir -p ~/Library/LaunchAgents
   - cp launchctl/com.ow.n8n.plist ~/Library/LaunchAgents/
   - launchctl load ~/Library/LaunchAgents/com.ow.n8n.plist
6) Stoppen:
   - docker compose down
7) Update:
   - docker compose pull && docker compose up -d
8) Uninstall:
   - docker compose down -v
   - rm -rf ./n8n_data ./postgres_data
   - launchctl unload ~/Library/LaunchAgents/com.ow.n8n.plist && rm ~/Library/LaunchAgents/com.ow.n8n.plist
