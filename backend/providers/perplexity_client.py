"""
Perplexity Provider Client
⚠️ Model default = "sonar" (not sonar-medium-online)
"""
import asyncio
import time
from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider, ProviderType, ProviderResponse, ProviderError


class PerplexityProvider(BaseProvider):
    """Perplexity API provider implementation"""
    
    def __init__(self, api_key: str, model: str = "sonar"):
        super().__init__(api_key, model)
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    def get_provider_type(self) -> ProviderType:
        return ProviderType.PERPLEXITY
    
    def get_default_model(self) -> str:
        return "sonar"  # ⚠️ Default model = "sonar"
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> ProviderResponse:
        """Generate response using Perplexity API"""
        start_time = time.time()
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            response = await self.client.post(
                self.base_url,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            
            usage_data = data.get("usage", {})
            tokens_in = usage_data.get("prompt_tokens", 0)
            tokens_out = usage_data.get("completion_tokens", 0)
            finish_reason = data["choices"][0].get("finish_reason")
            
            return self.create_success_response(
                content=data["choices"][0]["message"]["content"],
                usage=usage_data,
                metadata={
                    "finish_reason": finish_reason,
                    "model": data["model"]
                },
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return self.create_error_response(e, latency_ms)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Perplexity API health"""
        start_time = time.time()
        
        try:
            # Simple test request to check API health
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = await self.client.post(
                self.base_url,
                json=test_payload
            )
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "provider": "perplexity",
                "model": self.model
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "provider": "perplexity",
                "model": self.model,
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
