# backend/app/main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from .api.v1_rico import router as rico_router
from .routers.autopilot import router as autopilot_router
from .routers.monitor import router as monitor_router
from ..api.v2.autopilot import router as v2_autopilot_router
try:
    from ..v2.core.api import router as v2_core_router
except ImportError:
    # Fallback für externe Ausführung
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from backend.v2.core.api import router as v2_core_router
from .config import OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY, ENV_SOURCE

app = FastAPI(
    title="Rico 4.0 Orchestrator",
    docs_url="/api/v1/docs",        # Swagger
    redoc_url="/api/v1/redoc"       # Redoc (optional)
)

# CORS für Streamlit + Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "agent": "Rico 4.0"}

@app.get("/check-keys")
def check_keys():
    """Health-Check 2.0: Mini-Pings für alle Provider"""
    from .services.health_check import health_check_2
    
    # Verwende Health-Check 2.0 für einheitliches Schema
    import asyncio
    
    try:
        # Async Health-Check ausführen
        result = asyncio.run(health_check_2.check_all_providers())
        
        # Schema für Frontend-Kompatibilität
        providers = result.get("providers", {})
        
        return {
            "openai": providers.get("openai", {}).get("status", "unknown"),
            "claude": providers.get("claude", {}).get("status", "unknown"),
            "perplexity": providers.get("perplexity", {}).get("status", "unknown"),
            "env_source": ENV_SOURCE,
            "models": {
                "openai": providers.get("openai", {}).get("model", ""),
                "claude": providers.get("claude", {}).get("model", ""),
                "perplexity": providers.get("perplexity", {}).get("model", ""),
            },
            "latency": {
                "openai": providers.get("openai", {}).get("latency_ms", 0),
                "claude": providers.get("claude", {}).get("latency_ms", 0),
                "perplexity": providers.get("perplexity", {}).get("latency_ms", 0),
            }
        }
    except Exception as e:
        # Fallback bei Fehlern
        return {
            "openai": "error",
            "claude": "error", 
            "perplexity": "error",
            "env_source": ENV_SOURCE,
            "models": {
                "openai": "",
                "claude": "",
                "perplexity": "",
            },
            "error": str(e)
        }

# Router einbinden
app.include_router(rico_router, prefix="/api/v1")
app.include_router(autopilot_router)
app.include_router(monitor_router)
app.include_router(v2_core_router)
app.include_router(v2_autopilot_router)

# v2 Router
try:
    from ..v2.practice.api import router as v2_practice_router
    from ..v2.finance.api import router as v2_finance_router
    from ..v2.cashbot.api import router as v2_cashbot_router
    app.include_router(v2_practice_router)
    app.include_router(v2_finance_router)
    app.include_router(v2_cashbot_router)
except ImportError:
    # Fallback für externe Ausführung
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from backend.v2.practice.api import router as v2_practice_router
    from backend.v2.finance.api import router as v2_finance_router
    from backend.v2.cashbot.api import router as v2_cashbot_router
    app.include_router(v2_practice_router)
    app.include_router(v2_finance_router)
    app.include_router(v2_cashbot_router)