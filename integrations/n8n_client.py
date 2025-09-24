"""
n8n Event Hub Client
Sendet Events von Rico Backend an n8n Webhook für Orchestrierung
"""
import os
import logging
import httpx
from typing import Dict, Any

# Konfiguration über ENV-Variablen
N8N_ENABLED = os.getenv("N8N_ENABLED", "false").lower() == "true"
N8N_EVENT_WEBHOOK = os.getenv("N8N_EVENT_WEBHOOK", "http://localhost:5678/webhook/rico-events")
TIMEOUT = int(os.getenv("N8N_TIMEOUT_SECONDS", "20"))

# Logger für n8n Client
logger = logging.getLogger(__name__)

async def send_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sendet ein Event an den n8n Event Hub
    
    Args:
        event: Event-Dictionary mit type, data, source etc.
        
    Returns:
        Dictionary mit Status-Informationen
    """
    # Schutz: Wenn n8n nicht aktiviert ist
    if not N8N_ENABLED:
        logger.info("n8n disabled (N8N_ENABLED != true), skipping event dispatch")
        return {"ok": False, "reason": "n8n disabled"}
    
    logger.debug(f"Sending event to n8n: {event.get('type', 'unknown')}")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {
                "x-backend-base": os.getenv("BACKEND_BASE", "http://localhost:8000"),
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                N8N_EVENT_WEBHOOK, 
                json=event, 
                headers=headers
            )
            
            # Status-Code Mapping für klare Fehlertexte
            if response.status_code in (200, 204):
                logger.debug(f"Event sent successfully to n8n (status {response.status_code})")
                return {
                    "ok": True,
                    "status": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                }
            elif response.status_code == 401:
                logger.error("n8n authentication failed (401)")
                return {"ok": False, "reason": "authentication_failed", "status": 401}
            elif response.status_code == 403:
                logger.error("n8n access forbidden (403)")
                return {"ok": False, "reason": "access_forbidden", "status": 403}
            elif response.status_code == 404:
                logger.error("n8n webhook not found (404)")
                return {"ok": False, "reason": "webhook_not_found", "status": 404}
            elif response.status_code == 429:
                logger.warning("n8n rate limit exceeded (429)")
                return {"ok": False, "reason": "rate_limit_exceeded", "status": 429}
            elif response.status_code >= 500:
                logger.error(f"n8n server error ({response.status_code})")
                return {"ok": False, "reason": "server_error", "status": response.status_code}
            else:
                logger.warning(f"n8n unexpected response ({response.status_code})")
                return {"ok": False, "reason": "unexpected_response", "status": response.status_code}
            
    except httpx.TimeoutException:
        logger.error(f"n8n request timeout after {TIMEOUT}s")
        return {"ok": False, "reason": "timeout", "status": 408}
    except httpx.ConnectError:
        logger.error("n8n connection failed")
        return {"ok": False, "reason": "connection_failed", "status": 503}
    except httpx.HTTPError as e:
        logger.error(f"n8n HTTP error: {e}")
        return {"ok": False, "reason": f"http_error: {str(e)}", "status": 500}
    except Exception as e:
        logger.error(f"n8n unexpected error: {e}")
        return {"ok": False, "reason": f"unexpected_error: {str(e)}", "status": 500}