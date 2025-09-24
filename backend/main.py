"""
FastAPI App mit Router-Includes (/v1, /v2)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import subprocess
import os
import sys

from config.settings import settings
from utils.security import setup_secret_safe_logging, create_secret_safe_exception_handler
from api.health import router as health_router
from api.v1.main import router as v1_router
from api.v2.core import router as v2_core_router
from api.v2.cashbot import router as v2_cashbot_router
from api.v2.finance import router as v2_finance_router
from api.v2.practice import router as v2_practice_router
from api.v2.ai import router as v2_ai_router
from integrations.n8n_webhooks import router as webhooks_router


# Setup secret-safe logging
setup_secret_safe_logging()

# Create FastAPI app
app = FastAPI(
    title="Rico Orchestrator System",
    description="Backend API for Rico Orchestrator with provider parity and auto-race logic",
    version="2.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler
app.add_exception_handler(Exception, create_secret_safe_exception_handler())

# Include routers
app.include_router(health_router)
app.include_router(v1_router)
app.include_router(v2_core_router)
app.include_router(v2_cashbot_router)
app.include_router(v2_finance_router)
app.include_router(v2_practice_router)
app.include_router(v2_ai_router)
app.include_router(webhooks_router)

# Import integrations router after it's created
try:
    from api.v2.integrations import router as v2_integrations_router
    app.include_router(v2_integrations_router)
except ImportError:
    # Router wird später erstellt, ist OK
    pass


async def run_n8n_bootstrap():
    """Startet n8n Bootstrap als Subprozess"""
    n8n_enabled = os.getenv("N8N_ENABLED", "false").lower() == "true"
    
    if not n8n_enabled:
        logging.info("n8n disabled (N8N_ENABLED=false), skipping bootstrap")
        return
    
    try:
        # Bootstrap-Script ausführen
        bootstrap_script = os.path.join(os.path.dirname(__file__), "..", "integrations", "n8n", "bootstrap.py")
        
        # ENV-Variablen an Subprozess weitergeben
        env = os.environ.copy()
        
        logging.info("n8n bootstrap started")
        
        # Subprozess starten (nicht-blockierend)
        process = subprocess.Popen(
            [sys.executable, bootstrap_script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Output in Background loggen
        asyncio.create_task(log_bootstrap_output(process))
        
        logging.info("n8n bootstrap process started")
        
    except Exception as e:
        logging.error(f"Failed to start n8n bootstrap: {e}")


async def log_bootstrap_output(process):
    """Loggt Bootstrap-Output im Background"""
    try:
        stdout, stderr = await asyncio.get_event_loop().run_in_executor(
            None, process.communicate
        )
        
        if stdout:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    logging.info(f"n8n bootstrap: {line}")
        
        if stderr:
            for line in stderr.strip().split('\n'):
                if line.strip():
                    logging.error(f"n8n bootstrap error: {line}")
        
        if process.returncode == 0:
            logging.info("n8n bootstrap completed successfully")
        else:
            logging.warning(f"n8n bootstrap completed with code {process.returncode}")
            
    except Exception as e:
        logging.error(f"Error logging bootstrap output: {e}")


@app.on_event("startup")
async def startup_event():
    """FastAPI Startup Event"""
    logging.info("Rico Orchestrator System starting up...")
    
    # n8n Bootstrap starten (non-blocking)
    await run_n8n_bootstrap()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Rico Orchestrator System",
        "version": "2.0.0",
        "status": "running",
        "env_source": settings.env_source
    }


@app.get("/info")
async def info():
    """System information"""
    return {
        "app_name": settings.app_name,
        "version": "2.0.0",
        "env_source": settings.env_source,
        "debug": settings.debug,
        "providers_configured": {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "perplexity": bool(settings.perplexity_api_key)
        },
        "n8n_configured": bool(settings.n8n_webhook_url)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
