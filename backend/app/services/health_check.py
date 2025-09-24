"""
Rico 4.5 - Health Check 2.0
Mini-Pings für Provider mit Output-Schema (status, latency_ms, model, env_source)
"""

import os
import time
import asyncio
import httpx
from typing import Dict, Any, List

# Zentrale Config verwenden
from ..config import (
    OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY,
    OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL, ENV_SOURCE
)

# Mini-Ping Timeout (kurz für schnelle Checks)
from ..config import HEALTH_CHECK_TIMEOUT
PING_TIMEOUT = HEALTH_CHECK_TIMEOUT


class HealthCheck2:
    """Health Check 2.0 mit Mini-Pings für alle Provider"""
    
    def __init__(self):
        # Importiere die aktuellen Werte zur Laufzeit
        from ..config import OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY, OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL
        
        self.providers = {
            "openai": {
                "key": OPENAI_API_KEY,
                "model": OPENAI_MODEL,
                "url": "https://api.openai.com/v1/chat/completions",
                "headers": {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                "body": {
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                    "temperature": 0
                }
            },
            "claude": {
                "key": CLAUDE_API_KEY,
                "model": CLAUDE_MODEL,
                "url": "https://api.anthropic.com/v1/messages",
                "headers": {
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                "body": {
                    "model": CLAUDE_MODEL,
                    "max_tokens": 1,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": "ping"}]
                }
            },
            "perplexity": {
                "key": PPLX_API_KEY,
                "model": PPLX_MODEL,
                "url": "https://api.perplexity.ai/chat/completions",
                "headers": {"Authorization": f"Bearer {PPLX_API_KEY}", "Content-Type": "application/json"},
                "body": {
                    "model": PPLX_MODEL,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                    "temperature": 0
                }
            }
        }
    
    def _get_env_source(self, provider: str) -> str:
        """Bestimmt die Quelle der Umgebungsvariable"""
        from ..config import ENV_SOURCE
        return ENV_SOURCE
    
    def _map_error_to_status(self, error: str) -> str:
        """Mappt Fehler zu einheitlichen Status-Codes"""
        if "auth" in error.lower() or "401" in error:
            return "auth"
        elif "rate" in error.lower() or "429" in error:
            return "rate_limit"
        elif "timeout" in error.lower():
            return "timeout"
        elif "500" in error or "server" in error.lower():
            return "server"
        else:
            return "error"
    
    async def _ping_provider(self, provider: str) -> Dict[str, Any]:
        """Mini-Ping für einen Provider"""
        config = self.providers[provider]
        
        # Prüfe ob Key vorhanden
        if not config["key"]:
            from ..config import ENV_SOURCE
            return {
                "status": "N/A",
                "latency_ms": 0,
                "model": config["model"],
                "env_source": ENV_SOURCE,
                "error": "Key nicht gesetzt"
            }
        
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
                response = await client.post(
                    config["url"],
                    headers=config["headers"],
                    json=config["body"]
                )
                
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                
                if response.status_code == 200:
                    from ..config import ENV_SOURCE
                    return {
                        "status": "OK",
                        "latency_ms": latency_ms,
                        "model": config["model"],
                        "env_source": ENV_SOURCE,
                        "optional_models": [config["model"]]  # Könnte erweitert werden
                    }
                else:
                    from ..config import ENV_SOURCE
                    error_type = self._map_error_to_status(f"HTTP {response.status_code}")
                    return {
                        "status": error_type,
                        "latency_ms": latency_ms,
                        "model": config["model"],
                        "env_source": ENV_SOURCE,
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except httpx.TimeoutException:
            from ..config import ENV_SOURCE
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "status": "timeout",
                "latency_ms": latency_ms,
                "model": config["model"],
                "env_source": ENV_SOURCE,
                "error": "Timeout"
            }
        except Exception as e:
            from ..config import ENV_SOURCE
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            error_type = self._map_error_to_status(str(e))
            return {
                "status": error_type,
                "latency_ms": latency_ms,
                "model": config["model"],
                "env_source": ENV_SOURCE,
                "error": str(e)[:100]  # Begrenzte Fehlermeldung
            }
    
    async def check_all_providers(self) -> Dict[str, Any]:
        """Prüft alle Provider parallel"""
        tasks = []
        for provider in self.providers.keys():
            tasks.append(self._ping_provider(provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Ergebnisse zusammenfassen
        provider_results = {}
        for i, provider in enumerate(self.providers.keys()):
            if isinstance(results[i], Exception):
                from ..config import ENV_SOURCE
                provider_results[provider] = {
                    "status": "error",
                    "latency_ms": 0,
                    "model": self.providers[provider]["model"],
                    "env_source": ENV_SOURCE,
                    "error": str(results[i])[:100]
                }
            else:
                provider_results[provider] = results[i]
        
        return {
            "timestamp": time.time(),
            "providers": provider_results,
            "summary": {
                "total": len(self.providers),
                "ok": sum(1 for r in provider_results.values() if r["status"] == "OK"),
                "n_a": sum(1 for r in provider_results.values() if r["status"] == "N/A"),
                "errors": sum(1 for r in provider_results.values() if r["status"] not in ["OK", "N/A"])
            }
        }
    
    def get_keys_status(self) -> Dict[str, Any]:
        """Gibt Status der API-Keys zurück (ohne echte Calls)"""
        # Importiere die aktuellen Werte zur Laufzeit
        from ..config import OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY, OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL, ENV_SOURCE
        
        return {
            "openai": {
                "configured": bool(OPENAI_API_KEY),
                "env_source": ENV_SOURCE,
                "model": OPENAI_MODEL
            },
            "claude": {
                "configured": bool(CLAUDE_API_KEY),
                "env_source": ENV_SOURCE,
                "model": CLAUDE_MODEL
            },
            "perplexity": {
                "configured": bool(PPLX_API_KEY),
                "env_source": ENV_SOURCE,
                "model": PPLX_MODEL
            }
        }


# Globale Instanz
health_check_2 = HealthCheck2()
