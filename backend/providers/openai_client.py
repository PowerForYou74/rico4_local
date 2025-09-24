"""
OpenAI Provider Client
"""
import asyncio
import time
from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider, ProviderType, ProviderResponse, ProviderError


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    def get_provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    def get_default_model(self) -> str:
        return "gpt-3.5-turbo"
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> ProviderResponse:
        """Generate response using OpenAI API"""
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
                f"{self.base_url}/chat/completions",
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
        """Check OpenAI API health"""
        start_time = time.time()
        
        try:
            # Simple models list request to check API health
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "provider": "openai",
                "model": self.model,
                "available_models": len(response.json().get("data", []))
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "provider": "openai",
                "model": self.model,
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
