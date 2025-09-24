# backend/app/config.py
"""
Rico 4.5 - Zentrale Konfiguration
Load-Order: .env.local → .env
ENV_SOURCE wird gesetzt für Health-Check 2.0
"""

import os
from dotenv import load_dotenv

# ------------------------------------------------------------
# Env laden - .env.local hat Vorrang vor .env
# ------------------------------------------------------------
ENV_SOURCE = "runtime"  # Default

if os.path.exists(".env.local"):
    load_dotenv(".env.local")
    ENV_SOURCE = "local"
else:
    load_dotenv(".env")
    ENV_SOURCE = "env"

# Setze ENV_SOURCE als Umgebungsvariable für Health-Check
os.environ["ENV_SOURCE"] = ENV_SOURCE

# ------------------------------------------------------------
# API Keys
# ------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
PPLX_API_KEY = os.getenv("PPLX_API_KEY", "")

# ------------------------------------------------------------
# Model-Konfiguration
# ------------------------------------------------------------
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
PPLX_MODEL = os.getenv("PPLX_MODEL", "sonar")

# ------------------------------------------------------------
# Timeout und Retry-Konfiguration
# ------------------------------------------------------------
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "40"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "1"))

# ------------------------------------------------------------
# Performance-Optimierungen
# ------------------------------------------------------------
# Health-Check Timeout (kürzer für schnelle Checks)
HEALTH_CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", "5.0"))

# Auto-Race Timeout (für parallele Provider-Calls)
AUTO_RACE_TIMEOUT = float(os.getenv("AUTO_RACE_TIMEOUT", "30.0"))

# Cache-TTL für Health-Check (in Sekunden)
HEALTH_CHECK_CACHE_TTL = int(os.getenv("HEALTH_CHECK_CACHE_TTL", "10"))

# ------------------------------------------------------------
# Provider-Status
# ------------------------------------------------------------
def get_provider_status() -> dict:
    """Gibt Status aller Provider zurück"""
    return {
        "openai": {
            "configured": bool(OPENAI_API_KEY),
            "model": OPENAI_MODEL,
            "env_source": ENV_SOURCE
        },
        "claude": {
            "configured": bool(CLAUDE_API_KEY),
            "model": CLAUDE_MODEL,
            "env_source": ENV_SOURCE
        },
        "perplexity": {
            "configured": bool(PPLX_API_KEY),
            "model": PPLX_MODEL,
            "env_source": ENV_SOURCE
        }
    }
