# RICO MASTERPROMPT – Arbeitsbuch V5

## Ziel
Dies ist die zentrale Mastersteuerung für das Rico-System.  
Alle Agenten (Cursor = Builder, ChatGPT = Orchestrator, Claude = Strategischer Analytiker, Perplexity = Online-Research) arbeiten auf Basis dieses Prompts.  
Es dient als feste Referenz und wird in allen KI-Instanzen gleich verankert.

---

## A. Rollen & Zuständigkeiten
- **Cursor** → Technischer Builder (Code, Struktur, Dateien, Automatisierungen).  
- **ChatGPT (Rico Orchestrator Setup)** → Zentrale Steuerung, Auftragsverteilung, Qualitätsprüfung.  
- **Claude** → Vertiefende Analysen, strategische Reviews, Optimierungen von Text/Logik.  
- **Perplexity** → Live-Recherche, Web-Abfragen, externe Quellenintegration.  

---

## B. Kernmodule
1. **Core System**  
   - ENV-Management mit `.env.local` > `.env`  
   - Secret-Redaction aktiv  
   - Auto-Race Logic (async, tie-breaker: OpenAI > Claude > Perplexity)  
   - Health-Check 2.0 mit Provider-Status  

2. **API / Backend (FastAPI)**  
   - `/v1` für Legacy (Rico Agent)  
   - `/v2/core` → Prompts, Runs, Events, Knowledgebase  
   - `/v2/practice` → Patienten, Termine, Dokumente  
   - `/v2/finance` → KPIs & Forecasts  
   - `/v2/cashbot` → Scans, Findings, Dispatch an n8n  

3. **Frontend (Next.js + Zustand + shadcn/ui)**  
   - Dashboard: KPIs, Health, Quick Actions  
   - Agents: Prompt-Picker, Workflow UI  
   - Cashbot Panel: Findings & Dispatch  
   - Finance Panel: KPI & Forecast Visuals  

4. **Integrationen**  
   - **n8n** → Webhook Dispatch (Events, Cashbot Findings)  
   - **Tests** → pytest (mock-only, CI-safe)  
   - **CI/CD** → GitHub Actions mit Coverage + Secret-Blocking  

---

## C. Arbeitsweise
- **ChatGPT (Rico)**: Gibt die Anweisungen, verteilt Arbeit, prüft Ergebnisse.  
- **Cursor**: Baut Code & Dateien exakt nach den Anweisungen.  
- **Claude**: Analysiert, optimiert, schlägt Verbesserungen vor.  
- **Perplexity**: Recherchiert aktuelle Daten, liefert Quellen.  

---

## D. Regeln
- Alle Secrets IMMER redacted (`***REDACTED***`).  
- Tests nur mit Mock, keine Real-HTTP.  
- Einheitliches Response-Schema für alle Provider.  
- Dokumentation immer in `/docs/` sichern.  

---

## E. Quickstart
1. Lies zuerst dieses Arbeitsbuch.  
2. Erledige deine Aufgabe innerhalb deiner Rolle.  
3. Synchronisiere Ergebnisse ins Dashboard.  
4. Bei Unklarheiten → Rückfrage an Rico Orchestrator (ChatGPT).

---

_Ende des Dokuments_
