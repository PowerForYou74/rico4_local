"""
Health-Check 2.0: Schema {status, latency_ms, model, env_source}
"""
import time
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from ..config.settings import settings
from ..providers.openai_client import OpenAIProvider
from ..providers.anthropic_client import AnthropicProvider
from ..providers.perplexity_client import PerplexityProvider
from ..orchestrator.auto_race import AutoRaceOrchestrator


router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Individual provider health status"""
    provider: str
    model: str
    status: str
    latency_ms: float
    env_source: str = "unknown"
    error: str = None


class SystemHealth(BaseModel):
    """Overall system health status"""
    status: str
    latency_ms: float
    model: str
    env_source: str
    providers: List[HealthStatus]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.get("/", response_model=SystemHealth)
async def health_check():
    """Health-Check 2.0 with provider status"""
    start_time = time.time()
    
    # Initialize providers
    providers = []
    provider_health = []
    
    # OpenAI Provider
    if settings.openai_api_key:
        openai_provider = OpenAIProvider(settings.openai_api_key)
        providers.append(openai_provider)
        try:
            openai_health = await openai_provider.health_check()
            provider_health.append(HealthStatus(
                provider="openai",
                model=openai_provider.model,
                status=openai_health.get("status", "unknown"),
                latency_ms=openai_health.get("latency_ms", 0.0),
                env_source=settings.env_source,
                error=openai_health.get("error")
            ))
        except Exception as e:
            provider_health.append(HealthStatus(
                provider="openai",
                model=openai_provider.model,
                status="unhealthy",
                latency_ms=0.0,
                env_source=settings.env_source,
                error=str(e)
            ))
    
    # Anthropic Provider
    if settings.anthropic_api_key:
        anthropic_provider = AnthropicProvider(settings.anthropic_api_key)
        providers.append(anthropic_provider)
        try:
            anthropic_health = await anthropic_provider.health_check()
            provider_health.append(HealthStatus(
                provider="anthropic",
                model=anthropic_provider.model,
                status=anthropic_health.get("status", "unknown"),
                latency_ms=anthropic_health.get("latency_ms", 0.0),
                env_source=settings.env_source,
                error=anthropic_health.get("error")
            ))
        except Exception as e:
            provider_health.append(HealthStatus(
                provider="anthropic",
                model=anthropic_provider.model,
                status="unhealthy",
                latency_ms=0.0,
                env_source=settings.env_source,
                error=str(e)
            ))
    
    # Perplexity Provider
    if settings.perplexity_api_key:
        perplexity_provider = PerplexityProvider(settings.perplexity_api_key)
        providers.append(perplexity_provider)
        try:
            perplexity_health = await perplexity_provider.health_check()
            provider_health.append(HealthStatus(
                provider="perplexity",
                model=perplexity_provider.model,
                status=perplexity_health.get("status", "unknown"),
                latency_ms=perplexity_health.get("latency_ms", 0.0),
                env_source=settings.env_source,
                error=perplexity_health.get("error")
            ))
        except Exception as e:
            provider_health.append(HealthStatus(
                provider="perplexity",
                model=perplexity_provider.model,
                status="unhealthy",
                latency_ms=0.0,
                env_source=settings.env_source,
                error=str(e)
            ))
    
    # Calculate overall status
    total_latency_ms = (time.time() - start_time) * 1000
    healthy_providers = [p for p in provider_health if p.status == "healthy"]
    
    if not providers:
        overall_status = "no_providers"
        default_model = "none"
    elif healthy_providers:
        overall_status = "healthy"
        # Use first healthy provider's model
        default_model = healthy_providers[0].model
    else:
        overall_status = "unhealthy"
        # Use first provider's model as fallback
        default_model = provider_health[0].model if provider_health else "none"
    
    # Clean up providers
    for provider in providers:
        if hasattr(provider, 'close'):
            await provider.close()
    
    return SystemHealth(
        status=overall_status,
        latency_ms=total_latency_ms,
        model=default_model,
        env_source=settings.env_source,
        providers=provider_health
    )


@router.get("/providers")
async def providers_health():
    """Detailed health check for all providers"""
    providers = []
    
    if settings.openai_api_key:
        providers.append(OpenAIProvider(settings.openai_api_key))
    if settings.anthropic_api_key:
        providers.append(AnthropicProvider(settings.anthropic_api_key))
    if settings.perplexity_api_key:
        providers.append(PerplexityProvider(settings.perplexity_api_key))
    
    if not providers:
        return {"error": "No providers configured"}
    
    orchestrator = AutoRaceOrchestrator(providers)
    health_results = await orchestrator.health_check_all()
    
    # Clean up
    for provider in providers:
        if hasattr(provider, 'close'):
            await provider.close()
    
    return health_results


@router.get("/quick")
async def quick_health():
    """Quick health check without provider testing"""
    return {
        "status": "ok",
        "env_source": settings.env_source,
        "timestamp": datetime.utcnow().isoformat()
    }
