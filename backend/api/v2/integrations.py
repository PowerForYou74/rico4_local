"""
v2 Integrations API: n8n Status & Health
"""
import os
import httpx
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/v2/integrations", tags=["v2-integrations"])

# ENV-Konfiguration
N8N_ENABLED = os.getenv("N8N_ENABLED", "false").lower() == "true"
N8N_HOST = os.getenv("N8N_HOST", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY")
N8N_TIMEOUT_SECONDS = int(os.getenv("N8N_TIMEOUT_SECONDS", "15"))


class N8NStatus(BaseModel):
    """n8n Integration Status"""
    enabled: bool
    host: str
    reachable: bool
    api_key_present: bool
    last_check: datetime
    error_message: str = None


async def check_n8n_health() -> Dict[str, Any]:
    """Prüft n8n Health und gibt Status zurück"""
    if not N8N_ENABLED:
        return {
            "enabled": False,
            "host": N8N_HOST,
            "reachable": False,
            "api_key_present": False,
            "last_check": datetime.utcnow(),
            "error_message": "n8n disabled"
        }
    
    headers = {}
    if N8N_API_KEY:
        headers["X-N8N-API-KEY"] = N8N_API_KEY
    
    try:
        async with httpx.AsyncClient(timeout=N8N_TIMEOUT_SECONDS) as client:
            # Einfacher Health-Check - GET workflows
            response = await client.get(
                f"{N8N_HOST}/rest/workflows",
                headers=headers
            )
            
            reachable = response.status_code in (200, 401, 403)
            error_message = None
            
            if response.status_code == 401:
                error_message = "API authentication failed"
            elif response.status_code == 403:
                error_message = "API access forbidden"
            elif response.status_code not in (200, 401, 403):
                error_message = f"HTTP {response.status_code}"
            
            return {
                "enabled": True,
                "host": N8N_HOST,
                "reachable": reachable,
                "api_key_present": bool(N8N_API_KEY),
                "last_check": datetime.utcnow(),
                "error_message": error_message
            }
            
    except httpx.TimeoutException:
        return {
            "enabled": True,
            "host": N8N_HOST,
            "reachable": False,
            "api_key_present": bool(N8N_API_KEY),
            "last_check": datetime.utcnow(),
            "error_message": "Connection timeout"
        }
    except httpx.ConnectError:
        return {
            "enabled": True,
            "host": N8N_HOST,
            "reachable": False,
            "api_key_present": bool(N8N_API_KEY),
            "last_check": datetime.utcnow(),
            "error_message": "Connection failed"
        }
    except Exception as e:
        return {
            "enabled": True,
            "host": N8N_HOST,
            "reachable": False,
            "api_key_present": bool(N8N_API_KEY),
            "last_check": datetime.utcnow(),
            "error_message": str(e)
        }


@router.get("/n8n/status", response_model=N8NStatus)
async def get_n8n_status():
    """Gibt n8n Integration Status zurück"""
    status = await check_n8n_health()
    return N8NStatus(**status)


@router.get("/n8n/health")
async def get_n8n_health():
    """Einfacher Health-Check für n8n"""
    status = await check_n8n_health()
    
    if not status["enabled"]:
        return {"status": "disabled", "message": "n8n integration disabled"}
    
    if not status["reachable"]:
        return {
            "status": "error", 
            "message": f"n8n not reachable: {status['error_message']}"
        }
    
    if not status["api_key_present"]:
        return {
            "status": "warning",
            "message": "n8n reachable but no API key configured"
        }
    
    return {"status": "healthy", "message": "n8n integration working"}
