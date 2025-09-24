# backend/app/services/provider_clients.py
from ..config import (
    OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY,
    OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL,
    LLM_TIMEOUT_SECONDS, LLM_RETRIES
)
from .providers.claude_client import ClaudeClient
from .providers.pplx_client import PerplexityClient

def build_provider_client(name: str):
    """Erstellt Provider-spezifische Clients mit korrekten Headern"""
    n = name.lower()
    if n == "claude":
        api_key = CLAUDE_API_KEY
        model = CLAUDE_MODEL
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not set")
        return ClaudeClient(api_key, model, LLM_TIMEOUT_SECONDS, LLM_RETRIES)
    elif n == "perplexity":
        api_key = PPLX_API_KEY
        model = PPLX_MODEL
        if not api_key:
            raise ValueError("PPLX_API_KEY not set")
        return PerplexityClient(api_key, model, LLM_TIMEOUT_SECONDS, LLM_RETRIES)
    elif n == "openai":
        # Bestehende OpenAI-Implementierung beibehalten
        from .llm_clients import ask_openai
        return ask_openai
    else:
        raise ValueError(f"Unknown provider: {name}")
