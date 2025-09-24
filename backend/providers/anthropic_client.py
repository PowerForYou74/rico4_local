"""
Anthropic Provider Client
"""
import asyncio
import time
from typing import Dict, Any, Optional
import httpx
from .base import BaseProvider, ProviderType, ProviderResponse, ProviderError


class AnthropicProvider(BaseProvider):
    """Anthropic API provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
        self.base_url = "https://api.anthropic.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            timeout=30.0
        )
    
    def get_provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    def get_default_model(self) -> str:
        return "claude-3-sonnet-20240229"
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> ProviderResponse:
        """Generate response using Anthropic API"""
        start_time = time.time()
        
        try:
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            
            usage_data = data.get("usage", {})
            tokens_in = usage_data.get("input_tokens", 0)
            tokens_out = usage_data.get("output_tokens", 0)
            finish_reason = data.get("stop_reason")
            
            return self.create_success_response(
                content=data["content"][0]["text"],
                usage=usage_data,
                metadata={
                    "stop_reason": finish_reason,
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
        """Check Anthropic API health"""
        start_time = time.time()
        
        try:
            # Simple test request to check API health
            test_payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            response = await self.client.post(
                f"{self.base_url}/messages",
                json=test_payload
            )
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "provider": "anthropic",
                "model": self.model
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "provider": "anthropic",
                "model": self.model,
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
