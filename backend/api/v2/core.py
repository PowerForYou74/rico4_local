"""
v2 Core API: Prompts, Runs, KB, Events
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ...config.settings import settings
from ...providers.openai_client import OpenAIProvider
from ...providers.anthropic_client import AnthropicProvider
from ...providers.perplexity_client import PerplexityProvider
from ...orchestrator.auto_race import AutoRaceOrchestrator


router = APIRouter(prefix="/v2/core", tags=["v2-core"])


# Pydantic Models
class PromptRequest(BaseModel):
    """Prompt request model"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    provider: Optional[str] = None  # If None, use auto-race


class PromptResponse(BaseModel):
    """Prompt response model"""
    id: str
    content: str
    provider: str
    model: str
    usage: Dict[str, Any]
    latency_ms: float
    timestamp: datetime


class RunRequest(BaseModel):
    """Run request model"""
    name: str
    description: Optional[str] = None
    prompts: List[str]
    auto_race: bool = True


class RunResponse(BaseModel):
    """Run response model"""
    id: str
    name: str
    description: Optional[str]
    status: str
    results: List[PromptResponse]
    created_at: datetime


class KBEntry(BaseModel):
    """Knowledge Base entry"""
    id: str
    title: str
    content: str
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Event(BaseModel):
    """System event"""
    id: str
    type: str
    message: str
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventCreate(BaseModel):
    """Event creation request"""
    type: str
    data: Optional[Dict[str, Any]] = {}
    source: str = "backend"


# In-memory storage (in production, use database)
prompts_storage: Dict[str, PromptResponse] = {}
runs_storage: Dict[str, RunResponse] = {}
kb_storage: Dict[str, KBEntry] = {}
events_storage: List[Event] = []


def get_providers():
    """Get configured providers"""
    providers = []
    
    if settings.openai_api_key:
        providers.append(OpenAIProvider(settings.openai_api_key))
    if settings.anthropic_api_key:
        providers.append(AnthropicProvider(settings.anthropic_api_key))
    if settings.perplexity_api_key:
        providers.append(PerplexityProvider(settings.perplexity_api_key))
    
    return providers


@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptRequest):
    """Create a new prompt and get response"""
    providers = get_providers()
    
    if not providers:
        raise HTTPException(status_code=503, detail="No providers configured")
    
    prompt_id = str(uuid.uuid4())
    
    try:
        if request.provider and len(providers) > 0:
            # Use specific provider
            provider_map = {p.provider_type.value: p for p in providers}
            if request.provider not in provider_map:
                raise HTTPException(status_code=400, detail=f"Provider {request.provider} not available")
            
            provider = provider_map[request.provider]
            response = await provider.generate_response(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        else:
            # Use auto-race
            orchestrator = AutoRaceOrchestrator(providers)
            race_result = await orchestrator.race(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            if not race_result.winner:
                raise HTTPException(status_code=500, detail="All providers failed")
            
            response = race_result.winner
        
        # Store response
        prompt_response = PromptResponse(
            id=prompt_id,
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            latency_ms=response.latency_ms,
            timestamp=datetime.utcnow()
        )
        
        prompts_storage[prompt_id] = prompt_response
        
        # Log event
        events_storage.append(Event(
            id=str(uuid.uuid4()),
            type="prompt_created",
            message=f"Prompt created with {response.provider}",
            data={"prompt_id": prompt_id, "provider": response.provider}
        ))
        
        return prompt_response
        
    except Exception as e:
        # Log error event
        events_storage.append(Event(
            id=str(uuid.uuid4()),
            type="prompt_error",
            message=f"Prompt failed: {str(e)}",
            data={"prompt_id": prompt_id, "error": str(e)}
        ))
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up providers
        for provider in providers:
            if hasattr(provider, 'close'):
                await provider.close()


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get a specific prompt by ID"""
    if prompt_id not in prompts_storage:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompts_storage[prompt_id]


@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(limit: int = 50, offset: int = 0):
    """List all prompts"""
    prompts = list(prompts_storage.values())
    return prompts[offset:offset + limit]


@router.post("/runs", response_model=RunResponse)
async def create_run(request: RunRequest):
    """Create a new run with multiple prompts"""
    run_id = str(uuid.uuid4())
    results = []
    
    providers = get_providers()
    if not providers:
        raise HTTPException(status_code=503, detail="No providers configured")
    
    try:
        for prompt_text in request.prompts:
            if request.auto_race:
                # Use auto-race for each prompt
                orchestrator = AutoRaceOrchestrator(providers)
                race_result = await orchestrator.race(prompt_text)
                
                if race_result.winner:
                    results.append(PromptResponse(
                        id=str(uuid.uuid4()),
                        content=race_result.winner.content,
                        provider=race_result.winner.provider,
                        model=race_result.winner.model,
                        usage=race_result.winner.usage,
                        latency_ms=race_result.winner.latency_ms,
                        timestamp=datetime.utcnow()
                    ))
            else:
                # Use first available provider
                provider = providers[0]
                response = await provider.generate_response(prompt_text)
                
                results.append(PromptResponse(
                    id=str(uuid.uuid4()),
                    content=response.content,
                    provider=response.provider,
                    model=response.model,
                    usage=response.usage,
                    latency_ms=response.latency_ms,
                    timestamp=datetime.utcnow()
                ))
        
        run_response = RunResponse(
            id=run_id,
            name=request.name,
            description=request.description,
            status="completed",
            results=results,
            created_at=datetime.utcnow()
        )
        
        runs_storage[run_id] = run_response
        
        # Log event
        events_storage.append(Event(
            id=str(uuid.uuid4()),
            type="run_created",
            message=f"Run '{request.name}' completed with {len(results)} prompts",
            data={"run_id": run_id, "prompt_count": len(results)}
        ))
        
        return run_response
        
    except Exception as e:
        # Log error event
        events_storage.append(Event(
            id=str(uuid.uuid4()),
            type="run_error",
            message=f"Run failed: {str(e)}",
            data={"run_id": run_id, "error": str(e)}
        ))
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up providers
        for provider in providers:
            if hasattr(provider, 'close'):
                await provider.close()


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    """Get a specific run by ID"""
    if run_id not in runs_storage:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return runs_storage[run_id]


@router.get("/runs", response_model=List[RunResponse])
async def list_runs(limit: int = 50, offset: int = 0):
    """List all runs"""
    runs = list(runs_storage.values())
    return runs[offset:offset + limit]


@router.post("/kb", response_model=KBEntry)
async def create_kb_entry(title: str, content: str, tags: List[str] = []):
    """Create a new knowledge base entry"""
    entry_id = str(uuid.uuid4())
    
    entry = KBEntry(
        id=entry_id,
        title=title,
        content=content,
        tags=tags
    )
    
    kb_storage[entry_id] = entry
    
    # Log event
    events_storage.append(Event(
        id=str(uuid.uuid4()),
        type="kb_entry_created",
        message=f"KB entry '{title}' created",
        data={"entry_id": entry_id, "title": title}
    ))
    
    return entry


@router.get("/kb/{entry_id}", response_model=KBEntry)
async def get_kb_entry(entry_id: str):
    """Get a specific KB entry by ID"""
    if entry_id not in kb_storage:
        raise HTTPException(status_code=404, detail="KB entry not found")
    
    return kb_storage[entry_id]


@router.get("/kb", response_model=List[KBEntry])
async def search_kb(q: Optional[str] = None, tags: Optional[str] = None):
    """Search knowledge base"""
    entries = list(kb_storage.values())
    
    if q:
        entries = [e for e in entries if q.lower() in e.title.lower() or q.lower() in e.content.lower()]
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        entries = [e for e in entries if any(tag in e.tags for tag in tag_list)]
    
    return entries


@router.post("/events")
async def log_event(event: EventCreate):
    """Log a new event and send to n8n if enabled"""
    from integrations.n8n_client import send_event
    
    # Create event object
    event_id = str(uuid.uuid4())
    event_obj = Event(
        id=event_id,
        type=event.type,
        message=f"Event {event.type} from {event.source}",
        data=event.data
    )
    
    # Store event
    events_storage.append(event_obj)
    
    # Send to n8n
    dispatch = await send_event({
        "type": event.type, 
        "data": event.data or {}, 
        "source": event.source
    })
    
    return {"status": "logged", "n8n": dispatch}


@router.get("/events", response_model=List[Event])
async def get_events(limit: int = 100, event_type: Optional[str] = None):
    """Get system events"""
    events = events_storage.copy()
    
    if event_type:
        events = [e for e in events if e.type == event_type]
    
    # Return most recent events first
    events.sort(key=lambda x: x.timestamp, reverse=True)
    return events[:limit]
