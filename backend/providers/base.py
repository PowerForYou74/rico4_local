"""
Base provider interface with unified response schema and error mapping
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class ProviderType(str, Enum):
    """Supported provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"


class ProviderError(BaseModel):
    """Standardized provider error"""
    provider: str
    error_type: str
    message: str
    status_code: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProviderResponse(BaseModel):
    """Unified response schema for all providers"""
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    provider: str
    provider_model: str
    duration_s: float = 0.0
    finish_reason: Optional[str] = None
    # Legacy fields for compatibility
    model: str = ""
    usage: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[ProviderError] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        # Auto-populate legacy fields from new schema
        if 'model' not in data and 'provider_model' in data:
            data['model'] = data['provider_model']
        if 'latency_ms' not in data and 'duration_s' in data:
            data['latency_ms'] = data['duration_s'] * 1000
        super().__init__(**data)


class BaseProvider(ABC):
    """Base provider interface"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.provider_type = self.get_provider_type()
    
    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Get the provider type"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider"""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        **kwargs
    ) -> ProviderResponse:
        """Generate a response from the provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        pass
    
    def create_error_response(
        self, 
        error: Exception, 
        latency_ms: float = 0.0
    ) -> ProviderResponse:
        """Create standardized error response"""
        return ProviderResponse(
            provider=self.provider_type.value,
            model=self.model,
            content="",
            latency_ms=latency_ms,
            success=False,
            error=ProviderError(
                provider=self.provider_type.value,
                error_type=type(error).__name__,
                message=str(error)
            )
        )
    
    def create_success_response(
        self,
        content: str,
        usage: Dict[str, Any],
        metadata: Dict[str, Any],
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        finish_reason: Optional[str] = None
    ) -> ProviderResponse:
        """Create standardized success response"""
        duration_s = latency_ms / 1000.0
        return ProviderResponse(
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider=self.provider_type.value,
            provider_model=self.model,
            duration_s=duration_s,
            finish_reason=finish_reason,
            usage=usage,
            metadata=metadata,
            latency_ms=latency_ms,
            success=True
        )


class ProviderErrorMapper:
    """Maps provider-specific errors to standardized format"""
    
    ERROR_MAPPINGS = {
        "openai": {
            "RateLimitError": "rate_limit",
            "AuthenticationError": "auth_error",
            "InvalidRequestError": "invalid_request",
            "APIConnectionError": "connection_error",
            "Timeout": "timeout_error"
        },
        "anthropic": {
            "RateLimitError": "rate_limit",
            "AuthenticationError": "auth_error",
            "InvalidRequestError": "invalid_request",
            "APIConnectionError": "connection_error",
            "Timeout": "timeout_error"
        },
        "perplexity": {
            "RateLimitError": "rate_limit",
            "AuthenticationError": "auth_error",
            "InvalidRequestError": "invalid_request",
            "APIConnectionError": "connection_error",
            "Timeout": "timeout_error"
        }
    }
    
    @classmethod
    def map_error(cls, provider: str, error: Exception) -> str:
        """Map provider-specific error to standardized type"""
        provider_mappings = cls.ERROR_MAPPINGS.get(provider, {})
        error_name = type(error).__name__
        return provider_mappings.get(error_name, "unknown_error")
    
    @classmethod
    def get_error_message(cls, provider: str, error: Exception) -> str:
        """Get user-friendly error message"""
        error_type = cls.map_error(provider, error)
        
        error_messages = {
            "rate_limit": "API rate limit exceeded. Please try again later.",
            "auth_error": "Authentication failed. Please check your API key.",
            "invalid_request": "Invalid request parameters.",
            "connection_error": "Unable to connect to the API. Please check your internet connection.",
            "timeout_error": "Request timed out. Please try again.",
            "unknown_error": f"An unexpected error occurred: {str(error)}"
        }
        
        return error_messages.get(error_type, error_messages["unknown_error"])
