"""
v2 AI API: Multi-Provider Auto-Routing with /v2/ai/ask
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from ...config.settings import settings
from ...providers.openai_client import OpenAIProvider
from ...providers.anthropic_client import AnthropicProvider
from ...providers.perplexity_client import PerplexityProvider
from ...providers.base import ProviderType
from ...orchestrator.auto_race import AutoRaceOrchestrator

router = APIRouter(prefix="/v2/ai", tags=["v2-ai"])

# Logger
logger = logging.getLogger(__name__)


class AIAskRequest(BaseModel):
    """AI Ask request model"""
    task: str = Field(..., description="Task type: research|analysis|write|review")
    prompt: str = Field(..., description="The prompt/question to ask")
    preferred: str = Field(default="auto", description="Preferred provider: auto|openai|anthropic|perplexity")
    online: bool = Field(default=False, description="Whether online/research mode is needed")


class AIAskResponse(BaseModel):
    """AI Ask response model"""
    id: str
    content: str
    tokens_in: int
    tokens_out: int
    provider: str
    provider_model: str
    duration_s: float
    finish_reason: Optional[str]
    task: str
    routing_reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIHealthResponse(BaseModel):
    """AI Health response model"""
    providers: Dict[str, Dict[str, Any]]
    routing_rules: Dict[str, str]
    auto_race_enabled: bool


def get_available_providers() -> List:
    """Get configured providers"""
    providers = []
    
    if settings.openai_api_key:
        providers.append(OpenAIProvider(settings.openai_api_key))
    if settings.anthropic_api_key:
        providers.append(AnthropicProvider(settings.anthropic_api_key))
    if settings.perplexity_api_key:
        providers.append(PerplexityProvider(settings.perplexity_api_key))
    
    return providers


def determine_provider(request: AIAskRequest, available_providers: List) -> tuple:
    """Determine which provider to use based on routing rules"""
    
    # Force specific provider if requested
    if request.preferred != "auto":
        provider_map = {p.provider_type.value: p for p in available_providers}
        if request.preferred in provider_map:
            return provider_map[request.preferred], f"forced_{request.preferred}"
        else:
            raise HTTPException(status_code=400, detail=f"Provider {request.preferred} not available")
    
    # Auto-routing rules
    provider_map = {p.provider_type.value: p for p in available_providers}
    
    # Rule 1: Research or online mode → Perplexity
    if request.task == "research" or request.online:
        if ProviderType.PERPLEXITY.value in provider_map:
            return provider_map[ProviderType.PERPLEXITY.value], "research_online_mode"
    
    # Rule 2: Write or review → Anthropic
    if request.task in ["write", "review"]:
        if ProviderType.ANTHROPIC.value in provider_map:
            return provider_map[ProviderType.ANTHROPIC.value], "write_review_task"
    
    # Rule 3: Analysis (default) → OpenAI
    if request.task == "analysis" or request.task not in ["research", "write", "review"]:
        if ProviderType.OPENAI.value in provider_map:
            return provider_map[ProviderType.OPENAI.value], "analysis_default"
    
    # Fallback: Auto-race with all available providers
    if len(available_providers) > 1:
        return None, "auto_race_fallback"
    
    # Last resort: use first available provider
    if available_providers:
        return available_providers[0], "first_available"
    
    raise HTTPException(status_code=503, detail="No providers available")


@router.post("/ask", response_model=AIAskResponse)
async def ask_ai(request: AIAskRequest):
    """Ask AI with automatic provider routing"""
    
    # Get available providers
    available_providers = get_available_providers()
    if not available_providers:
        raise HTTPException(status_code=503, detail="No AI providers configured")
    
    # Determine provider and routing reason
    selected_provider, routing_reason = determine_provider(request, available_providers)
    
    response_id = str(uuid.uuid4())
    
    try:
        if selected_provider is None:
            # Auto-race mode
            logger.info(f"Running auto-race for task: {request.task}")
            orchestrator = AutoRaceOrchestrator(available_providers)
            race_result = await orchestrator.race(request.prompt)
            
            if not race_result.winner or not race_result.winner.success:
                raise HTTPException(status_code=500, detail="All providers failed in auto-race")
            
            winner = race_result.winner
            
            return AIAskResponse(
                id=response_id,
                content=winner.content,
                tokens_in=winner.tokens_in,
                tokens_out=winner.tokens_out,
                provider=winner.provider,
                provider_model=winner.provider_model,
                duration_s=winner.duration_s,
                finish_reason=winner.finish_reason,
                task=request.task,
                routing_reason=f"{routing_reason}_winner_{winner.provider}"
            )
        
        else:
            # Single provider mode
            logger.info(f"Using provider {selected_provider.provider_type.value} for task: {request.task}")
            response = await selected_provider.generate_response(request.prompt)
            
            if not response.success:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Provider {selected_provider.provider_type.value} failed: {response.error.message if response.error else 'Unknown error'}"
                )
            
            return AIAskResponse(
                id=response_id,
                content=response.content,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                provider=response.provider,
                provider_model=response.provider_model,
                duration_s=response.duration_s,
                finish_reason=response.finish_reason,
                task=request.task,
                routing_reason=routing_reason
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI ask failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")
    
    finally:
        # Clean up providers
        for provider in available_providers:
            if hasattr(provider, 'close'):
                await provider.close()


@router.get("/health", response_model=AIHealthResponse)
async def get_ai_health():
    """Get AI providers health status"""
    
    available_providers = get_available_providers()
    
    # Check health of all providers
    health_results = {}
    for provider in available_providers:
        try:
            health = await provider.health_check()
            health_results[provider.provider_type.value] = health
        except Exception as e:
            health_results[provider.provider_type.value] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Routing rules documentation
    routing_rules = {
        "research": "Perplexity (online research)",
        "analysis": "OpenAI (general analysis)",
        "write": "Anthropic (creative writing)",
        "review": "Anthropic (content review)",
        "online=true": "Perplexity (online mode)",
        "auto_race": "All providers (first success wins)"
    }
    
    return AIHealthResponse(
        providers=health_results,
        routing_rules=routing_rules,
        auto_race_enabled=len(available_providers) > 1
    )


@router.get("/routing-rules")
async def get_routing_rules():
    """Get detailed routing rules documentation"""
    
    return {
        "routing_logic": {
            "forced_provider": "If preferred != 'auto', use specified provider",
            "research_task": "research → Perplexity (sonar)",
            "online_mode": "online=true → Perplexity (sonar)",
            "write_review": "write|review → Anthropic (claude-3-7-sonnet-20250219)",
            "analysis_default": "analysis → OpenAI (gpt-4o)",
            "auto_race": "Fallback: All providers race (first success wins)",
            "tie_breaker": "openai > anthropic > perplexity"
        },
        "provider_models": {
            "openai": "gpt-4o (Chat Completions)",
            "anthropic": "claude-3-7-sonnet-20250219 (Messages API)",
            "perplexity": "sonar (Chat Completions)"
        },
        "response_schema": {
            "content": "string - AI response text",
            "tokens_in": "int - Input tokens used",
            "tokens_out": "int - Output tokens generated",
            "provider": "string - Provider used",
            "provider_model": "string - Specific model used",
            "duration_s": "float - Response time in seconds",
            "finish_reason": "string|null - Why generation stopped",
            "routing_reason": "string - Why this provider was chosen"
        }
    }
