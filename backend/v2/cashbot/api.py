from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import select, func
from datetime import datetime
from typing import List, Dict, Any
import json
import asyncio
from .models import CashbotFinding, CashbotConfig, FindingPriority, FindingStatus
from ..core.db import session
# from ...services.orchestrator import Orchestrator  # TODO: Fix import path
# from ...config import get_provider_status  # TODO: Fix import path

router = APIRouter(prefix="/v2/cashbot")

# Cashbot System Prompt
CASHBOT_SYSTEM_PROMPT = """
Du bist der RICO Cashbot - ein spezialisierter KI-Agent für Cashflow-Optimierung in der Tierheilpraxis.

AUFGABEN:
1. Kurzfristige Cashflow-Chancen identifizieren (Trends, Partnerschaften, lokale Events, digitale Produkte)
2. Bestehende Module analysieren (CellRepair, Futteranalysen): Lücken & Umsatzpotenzial
3. Konkurrenz/Preisbild beobachten, Handlungsempfehlungen priorisieren

AUSGABE-FORMAT (JSON):
{
  "title": "Kurzer Titel der Chance",
  "idea": "Detaillierte Beschreibung der Idee",
  "steps": ["Schritt 1", "Schritt 2", "Schritt 3"],
  "potential_eur": 1500.0,
  "effort": "low|medium|high",
  "risk": "low|medium|high", 
  "timeframe": "sofort|kurzfristig|mittel",
  "source_hints": ["Quelle 1", "Quelle 2"]
}

FOKUS: Praktische, umsetzbare Ideen für sofortige Umsatzsteigerung.
"""

async def run_cashbot_scan():
    """Interne Cashbot-Scan Funktion"""
    try:
        # TODO: Implementiere echte Orchestrator-Integration
        # Für jetzt Mock-Response
        return {
            "response": json.dumps({
                "title": "Digitale Futterberatung",
                "idea": "Online-Service für personalisierte Futterempfehlungen mit KI-Unterstützung",
                "steps": [
                    "Website mit KI-Chatbot erstellen",
                    "Futterdatenbank aufbauen",
                    "Marketing-Kampagne starten"
                ],
                "potential_eur": 2000.0,
                "effort": "medium",
                "risk": "low",
                "timeframe": "kurzfristig",
                "source_hints": ["KI-Analyse", "Markttrends"]
            }),
            "meta": {
                "used_provider": "claude",
                "duration_s": 3.2
            }
        }
        
    except Exception as e:
        print(f"Cashbot scan error: {e}")
        return None

@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks, s=Depends(session)):
    """Startet Cashbot-Scan im Hintergrund"""
    try:
        # Führe Scan aus
        result = await run_cashbot_scan()
        
        if not result or not result.get("response"):
            return {"status": "error", "message": "Scan failed"}
        
        # Parse JSON Response
        try:
            finding_data = json.loads(result["response"])
        except json.JSONDecodeError:
            # Fallback wenn kein JSON
            finding_data = {
                "title": "Cashflow-Analyse",
                "idea": result["response"],
                "steps": ["Analyse durchführen", "Umsetzung planen"],
                "potential_eur": 1000.0,
                "effort": "medium",
                "risk": "low",
                "timeframe": "kurzfristig",
                "source_hints": ["KI-Analyse"]
            }
        
        # Speichere Finding
        finding = CashbotFinding(
            title=finding_data.get("title", "Cashflow-Chance"),
            idea=finding_data.get("idea", ""),
            steps=json.dumps(finding_data.get("steps", [])),
            potential_eur=finding_data.get("potential_eur", 0.0),
            effort=finding_data.get("effort", "medium"),
            risk=finding_data.get("risk", "low"),
            timeframe=FindingPriority(finding_data.get("timeframe", "kurzfristig")),
            source_hints=json.dumps(finding_data.get("source_hints", [])),
            provider=result.get("meta", {}).get("used_provider", "unknown"),
            duration_s=result.get("meta", {}).get("duration_s", 0.0)
        )
        
        s.add(finding)
        s.commit()
        s.refresh(finding)
        
        return {
            "status": "success",
            "finding_id": finding.id,
            "title": finding.title,
            "potential_eur": finding.potential_eur
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/findings")
def list_findings(s=Depends(session)):
    """Liste aller Findings, priorisiert"""
    findings = s.exec(
        select(CashbotFinding)
        .order_by(CashbotFinding.potential_eur.desc())
        .limit(50)
    ).all()
    
    # Konvertiere JSON-Felder
    result = []
    for f in findings:
        result.append({
            "id": f.id,
            "title": f.title,
            "idea": f.idea,
            "steps": json.loads(f.steps) if f.steps else [],
            "potential_eur": f.potential_eur,
            "effort": f.effort,
            "risk": f.risk,
            "timeframe": f.timeframe,
            "status": f.status,
            "provider": f.provider,
            "duration_s": f.duration_s,
            "created_at": f.created_at,
            "dispatched_at": f.dispatched_at
        })
    
    return result

@router.get("/config")
def get_config(s=Depends(session)):
    """Cashbot-Konfiguration"""
    config = s.exec(select(CashbotConfig).limit(1)).first()
    
    if not config:
        # Erstelle Default-Config
        config = CashbotConfig()
        s.add(config)
        s.commit()
        s.refresh(config)
    
    # Provider-Status prüfen (Mock für jetzt)
    online_capable = False  # TODO: Implementiere echte Provider-Prüfung
    
    return {
        "interval_cron": config.interval_cron,
        "providers_enabled": json.loads(config.providers_enabled) if config.providers_enabled else ["openai", "claude"],
        "online_capable": online_capable,
        "last_scan": config.last_scan
    }

@router.post("/dispatch/{finding_id}")
def dispatch_finding(finding_id: int, s=Depends(session)):
    """Sende Finding an n8n"""
    finding = s.get(CashbotFinding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # TODO: Implementiere n8n-Webhook
    # Für jetzt nur Status-Update
    finding.status = FindingStatus.in_progress
    finding.dispatched_at = datetime.utcnow()
    s.add(finding)
    s.commit()
    
    return {
        "status": "dispatched",
        "finding_id": finding_id,
        "dispatched_at": finding.dispatched_at
    }
